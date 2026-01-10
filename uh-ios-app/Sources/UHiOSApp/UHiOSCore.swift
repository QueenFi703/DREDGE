//
// UHiOSCore.swift
// µH-iOS Application Core
//
// Swift wrapper around the Rust µH-iOS core, providing iOS application
// integration and Hypervisor.framework orchestration.
//

import Foundation

#if canImport(Hypervisor)
import Hypervisor
#endif

/// µH-iOS Core Manager
///
/// Coordinates between the Rust verification core and iOS/HVF runtime.
/// This class serves as the orchestration layer that enforces policy
/// while delegating verification to the Rust core.
public class UHiOSCore {
    
    // MARK: - Types
    
    /// VM Configuration
    public struct VMConfig {
        /// Memory size in bytes
        public let memorySize: UInt64
        
        /// Number of virtual CPUs
        public let vcpuCount: UInt32
        
        /// VM name for identification
        public let name: String
        
        public init(memorySize: UInt64 = 512 * 1024 * 1024, // 512 MB default
                   vcpuCount: UInt32 = 1,
                   name: String = "Guest VM") {
            self.memorySize = memorySize
            self.vcpuCount = vcpuCount
            self.name = name
        }
    }
    
    /// VM State
    public enum VMState {
        case created
        case runnable
        case running
        case trapped
        case halted
    }
    
    /// VM Handle
    public struct VMHandle {
        let id: UInt32
        let config: VMConfig
        
        internal init(id: UInt32, config: VMConfig) {
            self.id = id
            self.config = config
        }
    }
    
    // MARK: - Properties
    
    private var vms: [UInt32: VMHandle] = [:]
    private var nextVMID: UInt32 = 1
    private let queue = DispatchQueue(label: "com.uhios.core", qos: .userInitiated)
    
    /// Singleton instance
    public static let shared = UHiOSCore()
    
    private init() {
        // Initialize µH-iOS core
        // In production, this would initialize the Rust FFI bridge
    }
    
    // MARK: - VM Lifecycle
    
    /// Create a new virtual machine
    ///
    /// This method:
    /// 1. Allocates a VMID from the Rust core
    /// 2. Creates HVF VM instance
    /// 3. Initializes memory mappings
    /// 4. Sets up VCPU contexts
    ///
    /// - Parameter config: VM configuration
    /// - Returns: VM handle
    /// - Throws: UHiOSError on failure
    public func createVM(config: VMConfig = VMConfig()) throws -> VMHandle {
        return try queue.sync {
            // Allocate VMID from Rust core
            let vmid = nextVMID
            nextVMID += 1
            
            // In production: Call Rust FFI to create VM in core
            // let rustVMID = uh_ios_create_vm()
            
            #if canImport(Hypervisor) && (arch(arm64) || arch(x86_64))
            // Create HVF VM instance (macOS/iOS with HVF support)
            // let hvfResult = hv_vm_create(HV_VM_DEFAULT)
            // guard hvfResult == HV_SUCCESS else {
            //     throw UHiOSError.hvfError("Failed to create HVF VM")
            // }
            #endif
            
            let handle = VMHandle(id: vmid, config: config)
            vms[vmid] = handle
            
            return handle
        }
    }
    
    /// Initialize VM with CPU state
    ///
    /// Transitions VM from Created → Runnable state
    ///
    /// - Parameters:
    ///   - handle: VM handle
    ///   - entryPoint: Guest entry point address
    /// - Throws: UHiOSError on failure
    public func initializeVM(_ handle: VMHandle, entryPoint: UInt64) throws {
        try queue.sync {
            guard vms[handle.id] != nil else {
                throw UHiOSError.vmNotFound(handle.id)
            }
            
            // In production: Call Rust FFI to initialize VM
            // uh_ios_initialize_vm(handle.id, entryPoint)
            
            #if canImport(Hypervisor)
            // Initialize VCPU state via HVF
            // Set entry point, stack pointer, etc.
            #endif
        }
    }
    
    /// Run VM
    ///
    /// Executes VM until exit condition is met
    ///
    /// - Parameter handle: VM handle
    /// - Returns: Exit reason
    /// - Throws: UHiOSError on failure
    public func runVM(_ handle: VMHandle) throws -> ExitReason {
        return try queue.sync {
            guard vms[handle.id] != nil else {
                throw UHiOSError.vmNotFound(handle.id)
            }
            
            // In production: Call Rust FFI + HVF to run VM
            // let exitReason = uh_ios_run_vm(handle.id)
            
            #if canImport(Hypervisor)
            // Run VCPU via HVF
            // hv_vcpu_run(vcpu)
            // Get exit information
            #endif
            
            // Stub: Return WFI exit
            return .wfi
        }
    }
    
    /// Halt VM permanently
    ///
    /// Transitions VM to Halted state (terminal)
    ///
    /// - Parameter handle: VM handle
    /// - Throws: UHiOSError on failure
    public func haltVM(_ handle: VMHandle) throws {
        try queue.sync {
            guard vms[handle.id] != nil else {
                throw UHiOSError.vmNotFound(handle.id)
            }
            
            // In production: Call Rust FFI to halt VM
            // uh_ios_halt_vm(handle.id)
            
            #if canImport(Hypervisor)
            // Destroy HVF resources
            // hv_vm_destroy()
            #endif
        }
    }
    
    /// Destroy VM and clean up resources
    ///
    /// - Parameter handle: VM handle
    /// - Throws: UHiOSError on failure
    public func destroyVM(_ handle: VMHandle) throws {
        try queue.sync {
            guard vms[handle.id] != nil else {
                throw UHiOSError.vmNotFound(handle.id)
            }
            
            // In production: Call Rust FFI to destroy VM
            // uh_ios_destroy_vm(handle.id)
            
            vms.removeValue(forKey: handle.id)
        }
    }
    
    // MARK: - System Info
    
    /// Get system capabilities
    ///
    /// Checks HVF availability and supported features
    public func getSystemInfo() -> SystemInfo {
        var hvfAvailable = false
        
        #if canImport(Hypervisor)
        #if arch(arm64) || arch(x86_64)
        // Check HVF availability on supported architectures
        // In production: hv_vm_get_max_vcpu_count() etc.
        hvfAvailable = true
        #endif
        #endif
        
        return SystemInfo(
            hvfAvailable: hvfAvailable,
            platform: Platform.current,
            rustCoreVersion: "0.1.0"
        )
    }
}

// MARK: - Supporting Types

/// Exit reasons from VM execution
public enum ExitReason {
    case hypercall(nr: UInt64, args: [UInt64])
    case memoryFault(gpa: UInt64, write: Bool)
    case instructionAbort(gpa: UInt64)
    case systemRegister(reg: UInt32, write: Bool)
    case wfi
    case exception(vector: UInt32)
    case cancelled
}

/// System information
public struct SystemInfo {
    public let hvfAvailable: Bool
    public let platform: Platform
    public let rustCoreVersion: String
}

/// Platform identification
public enum Platform {
    case iOS
    case macOS
    case simulator
    case unknown
    
    static var current: Platform {
        #if os(iOS)
        #if targetEnvironment(simulator)
        return .simulator
        #else
        return .iOS
        #endif
        #elseif os(macOS)
        return .macOS
        #else
        return .unknown
        #endif
    }
}

/// µH-iOS Errors
public enum UHiOSError: Error, LocalizedError {
    case vmNotFound(UInt32)
    case invalidVMState(UInt32)
    case memoryError(String)
    case capabilityError(String)
    case hvfError(String)
    case unsupportedPlatform
    
    public var errorDescription: String? {
        switch self {
        case .vmNotFound(let id):
            return "VM \(id) not found"
        case .invalidVMState(let id):
            return "VM \(id) in invalid state"
        case .memoryError(let msg):
            return "Memory error: \(msg)"
        case .capabilityError(let msg):
            return "Capability error: \(msg)"
        case .hvfError(let msg):
            return "HVF error: \(msg)"
        case .unsupportedPlatform:
            return "Platform does not support virtualization"
        }
    }
}
