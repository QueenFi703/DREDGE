//
// UHiOSViewModel.swift
// µH-iOS View Model
//
// Manages application state and coordinates with µH-iOS core
//

import Foundation
import Combine

/// VM information for UI
public struct VMInfo: Identifiable {
    public let id: UInt32
    public let name: String
    public var state: State
    public let memorySize: UInt64
    public let vcpuCount: UInt32
    
    public enum State {
        case created
        case runnable
        case running
        case trapped
        case halted
    }
}

/// View model for µH-iOS application
public class UHiOSViewModel: ObservableObject {
    // MARK: - Published Properties
    
    @Published public private(set) var vms: [VMInfo] = []
    @Published public private(set) var systemInfo: SystemInfo
    @Published public private(set) var error: UHiOSError?
    
    // MARK: - Private Properties
    
    private let core = UHiOSCore.shared
    private var vmHandles: [UInt32: UHiOSCore.VMHandle] = [:]
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    
    public init() {
        self.systemInfo = core.getSystemInfo()
    }
    
    // MARK: - VM Operations
    
    /// Create a new virtual machine
    public func createVM(name: String, memorySize: UInt64, vcpuCount: UInt32) {
        do {
            let config = UHiOSCore.VMConfig(
                memorySize: memorySize,
                vcpuCount: vcpuCount,
                name: name
            )
            
            let handle = try core.createVM(config: config)
            
            let vmInfo = VMInfo(
                id: handle.id,
                name: name,
                state: .created,
                memorySize: memorySize,
                vcpuCount: vcpuCount
            )
            
            vmHandles[handle.id] = handle
            vms.append(vmInfo)
            
        } catch let error as UHiOSError {
            self.error = error
        } catch {
            self.error = .hvfError("Unknown error creating VM")
        }
    }
    
    /// Initialize a VM
    public func initializeVM(_ vm: VMInfo, entryPoint: UInt64 = 0x1000) {
        guard let handle = vmHandles[vm.id] else {
            self.error = .vmNotFound(vm.id)
            return
        }
        
        do {
            try core.initializeVM(handle, entryPoint: entryPoint)
            updateVMState(vm.id, state: .runnable)
        } catch let error as UHiOSError {
            self.error = error
        } catch {
            self.error = .hvfError("Unknown error initializing VM")
        }
    }
    
    /// Run a VM
    public func runVM(_ vm: VMInfo) {
        guard let handle = vmHandles[vm.id] else {
            self.error = .vmNotFound(vm.id)
            return
        }
        
        // Update state to running
        updateVMState(vm.id, state: .running)
        
        // Run VM asynchronously
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            do {
                let exitReason = try self?.core.runVM(handle)
                
                DispatchQueue.main.async {
                    // Handle exit reason
                    self?.handleVMExit(vm.id, exitReason: exitReason)
                }
            } catch let error as UHiOSError {
                DispatchQueue.main.async {
                    self?.error = error
                    self?.updateVMState(vm.id, state: .trapped)
                }
            } catch {
                DispatchQueue.main.async {
                    self?.error = .hvfError("Unknown error running VM")
                    self?.updateVMState(vm.id, state: .trapped)
                }
            }
        }
    }
    
    /// Halt a VM
    public func haltVM(_ vm: VMInfo) {
        guard let handle = vmHandles[vm.id] else {
            self.error = .vmNotFound(vm.id)
            return
        }
        
        do {
            try core.haltVM(handle)
            updateVMState(vm.id, state: .halted)
        } catch let error as UHiOSError {
            self.error = error
        } catch {
            self.error = .hvfError("Unknown error halting VM")
        }
    }
    
    /// Destroy a VM
    public func destroyVM(_ vm: VMInfo) {
        guard let handle = vmHandles[vm.id] else {
            self.error = .vmNotFound(vm.id)
            return
        }
        
        do {
            try core.destroyVM(handle)
            vmHandles.removeValue(forKey: vm.id)
            vms.removeAll { $0.id == vm.id }
        } catch let error as UHiOSError {
            self.error = error
        } catch {
            self.error = .hvfError("Unknown error destroying VM")
        }
    }
    
    // MARK: - Private Helpers
    
    private func updateVMState(_ vmid: UInt32, state: VMInfo.State) {
        if let index = vms.firstIndex(where: { $0.id == vmid }) {
            vms[index].state = state
        }
    }
    
    private func handleVMExit(_ vmid: UInt32, exitReason: ExitReason?) {
        guard let exitReason = exitReason else {
            updateVMState(vmid, state: .trapped)
            return
        }
        
        switch exitReason {
        case .wfi:
            // WFI - VM yielded, can resume
            updateVMState(vmid, state: .runnable)
            
        case .hypercall(let nr, _):
            if nr == 1 {
                // Halt hypercall
                updateVMState(vmid, state: .halted)
            } else {
                updateVMState(vmid, state: .trapped)
            }
            
        case .memoryFault, .instructionAbort, .systemRegister, .exception:
            // VM trapped with exception
            updateVMState(vmid, state: .trapped)
            
        case .cancelled:
            // VM cancelled
            updateVMState(vmid, state: .halted)
        }
    }
    
    /// Refresh system information
    public func refreshSystemInfo() {
        systemInfo = core.getSystemInfo()
    }
}
