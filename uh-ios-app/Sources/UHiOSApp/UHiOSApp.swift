//
// UHiOSApp.swift
// µH-iOS Application Entry Point
//
// SwiftUI application providing user interface for µH-iOS
//

import SwiftUI

/// Main application structure
@main
public struct UHiOSApplication: App {
    @StateObject private var viewModel = UHiOSViewModel()
    
    public init() {}
    
    public var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(viewModel)
        }
    }
}

/// Main content view
public struct ContentView: View {
    @EnvironmentObject private var viewModel: UHiOSViewModel
    
    public var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                Text("µH-iOS")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Formally Verified Micro-Hypervisor")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                Divider()
                
                // System Info
                SystemInfoView()
                
                Divider()
                
                // VM Management
                VMManagementView()
                
                Spacer()
            }
            .padding()
            .navigationTitle("µH-iOS")
        }
    }
}

/// System information display
struct SystemInfoView: View {
    @EnvironmentObject private var viewModel: UHiOSViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("System Information")
                .font(.headline)
            
            HStack {
                Text("Platform:")
                Spacer()
                Text(viewModel.systemInfo.platform.description)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                Text("HVF Available:")
                Spacer()
                Image(systemName: viewModel.systemInfo.hvfAvailable ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(viewModel.systemInfo.hvfAvailable ? .green : .red)
            }
            
            HStack {
                Text("Core Version:")
                Spacer()
                Text(viewModel.systemInfo.rustCoreVersion)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(10)
    }
}

/// VM management interface
struct VMManagementView: View {
    @EnvironmentObject private var viewModel: UHiOSViewModel
    @State private var showingCreateVM = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Virtual Machines")
                    .font(.headline)
                Spacer()
                Button(action: { showingCreateVM = true }) {
                    Image(systemName: "plus.circle.fill")
                        .font(.title2)
                }
                .disabled(!viewModel.systemInfo.hvfAvailable)
            }
            
            if viewModel.vms.isEmpty {
                Text("No VMs created")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                ForEach(viewModel.vms) { vm in
                    VMRowView(vm: vm)
                }
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(10)
        .sheet(isPresented: $showingCreateVM) {
            CreateVMView()
                .environmentObject(viewModel)
        }
    }
}

/// Individual VM row
struct VMRowView: View {
    let vm: VMInfo
    @EnvironmentObject private var viewModel: UHiOSViewModel
    
    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(vm.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text("ID: \(vm.id)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Text(vm.state.description)
                .font(.caption)
                .padding(6)
                .background(vm.state.color.opacity(0.2))
                .cornerRadius(6)
            
            Menu {
                Button("Run") {
                    viewModel.runVM(vm)
                }
                Button("Halt", role: .destructive) {
                    viewModel.haltVM(vm)
                }
            } label: {
                Image(systemName: "ellipsis.circle")
            }
        }
        .padding(10)
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(8)
    }
}

/// Create VM sheet
struct CreateVMView: View {
    @EnvironmentObject private var viewModel: UHiOSViewModel
    @Environment(\.dismiss) private var dismiss
    
    @State private var vmName = "Guest VM"
    @State private var memorySize = 512 // MB
    @State private var vcpuCount = 1
    
    var body: some View {
        NavigationView {
            Form {
                Section("Configuration") {
                    TextField("VM Name", text: $vmName)
                    
                    Picker("Memory (MB)", selection: $memorySize) {
                        Text("256 MB").tag(256)
                        Text("512 MB").tag(512)
                        Text("1 GB").tag(1024)
                        Text("2 GB").tag(2048)
                    }
                    
                    Stepper("VCPUs: \(vcpuCount)", value: $vcpuCount, in: 1...4)
                }
            }
            .navigationTitle("Create VM")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        viewModel.createVM(
                            name: vmName,
                            memorySize: UInt64(memorySize) * 1024 * 1024,
                            vcpuCount: UInt32(vcpuCount)
                        )
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - Preview

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(UHiOSViewModel())
    }
}

// MARK: - Extensions

extension Platform {
    var description: String {
        switch self {
        case .iOS: return "iOS"
        case .macOS: return "macOS"
        case .simulator: return "Simulator"
        case .unknown: return "Unknown"
        }
    }
}

extension VMInfo.State {
    var description: String {
        switch self {
        case .created: return "Created"
        case .runnable: return "Runnable"
        case .running: return "Running"
        case .trapped: return "Trapped"
        case .halted: return "Halted"
        }
    }
    
    var color: Color {
        switch self {
        case .created: return .blue
        case .runnable: return .green
        case .running: return .orange
        case .trapped: return .yellow
        case .halted: return .red
        }
    }
}
