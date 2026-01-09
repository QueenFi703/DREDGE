// µH-iOS Hypervisor.framework Bridge (C++ Header)
//
// This header provides C++ wrappers for Hypervisor.framework APIs
// to be used via cxx bridge from Rust

#pragma once

#include <cstdint>
#include <memory>

namespace uhios {
namespace hvf {

// VM context structure (complete definition needed for cxx unique_ptr)
struct VMContext {
    uint32_t vmid;
    // In production: hv_vm_t vm_handle;
    // In production: std::vector<hv_vcpu_t> vcpus;
};

// Global functions callable from Rust via cxx bridge
std::unique_ptr<VMContext> create_vm(uint32_t vmid);
void destroy_vm(std::unique_ptr<VMContext> ctx);

bool create_vcpu(VMContext& ctx, uint32_t vcpu_id);
bool destroy_vcpu(VMContext& ctx, uint32_t vcpu_id);

bool map_memory(VMContext& ctx, uint64_t gpa, uint64_t hva, uint64_t size);
bool unmap_memory(VMContext& ctx, uint64_t gpa, uint64_t size);

} // namespace hvf
} // namespace uhios
