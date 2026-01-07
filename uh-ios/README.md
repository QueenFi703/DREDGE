# µH-iOS: A Formally Verified Micro-Hypervisor Nucleus for iOS

**Authors:** Fi, Ziggy  
**Affiliation:** Independent Research  
**Version:** 0.1.0

---

## Overview

µH-iOS is a formally verified micro-hypervisor nucleus designed to operate within the constraints of Apple's iOS platform. Unlike traditional hypervisors that execute beneath the host operating system, µH-iOS is implemented as a minimal, verifiable isolation core running in user space and backed by Apple's Hypervisor.framework (HVF).

## Architecture

The system is organized into six core modules:

### 1. Types Module (`types.rs`)
Defines the formal system model including:
- **SystemState (Σ)**: Complete system state with VMs, memory mappings, capabilities, and exit queue
- **VMState**: State machine with explicit states (Created, Runnable, Trapped, Halted)
- **VMID**: Virtual Machine identifier
- **GPA/HostPage**: Guest physical address and host page mapping types
- **Capability**: Explicit capability types for access control
- **ExitReason**: Enumeration of all possible VM exit conditions

### 2. VM Module (`vm.rs`)
Implements VM lifecycle management with formally proven state transitions:
- `create_vm()`: ∅ → Created
- `initialize_vm()`: Created → Runnable(CPUState)
- `trap_vm()`: Runnable → Trapped(ExitReason, CPUState)
- `resume_vm()`: Trapped → Runnable(CPUState)
- `halt_vm()`: * → Halted (terminal state)

All transitions enforce capability requirements and maintain system invariants.

### 3. Memory Module (`memory.rs`)
Enforces memory non-interference invariant:
- Maps guest physical addresses to host pages
- Verifies no two VMs share memory regions
- Maintains invariant: ∀ vm₁ vm₂. vm₁ ≠ vm₂ → memory(vm₁) ∩ memory(vm₂) = ∅

### 4. Capability Module (`capability.rs`)
Enforces capability soundness:
- Checks capability possession before operations
- Grants and revokes capabilities
- Transfers capabilities between VMs
- Invariant: Action occurs ↔ VM possesses required capability

### 5. Exit Module (`exit.rs`)
Implements deterministic VM exit handling:
- **Totality**: All exit reasons explicitly handled
- **Determinism**: Same (vmid, exit, cpu_state) → same action
- Handles: Hypercalls, Memory Faults, Instruction Aborts, System Register Access, WFI, Exceptions

### 6. HVF Module (`hvf.rs`)
FFI bindings to Apple's Hypervisor.framework:
- VM creation/destruction
- VCPU management
- Memory mapping operations
- CPU state get/set
- VM execution

Note: Current implementation provides stub interfaces for formal modeling. Production implementation would link to actual HVF APIs.

## Formal Properties

### Invariant 1: Memory Non-Interference
```
∀ vm₁ vm₂ ∈ VMs. vm₁ ≠ vm₂ → memory(vm₁) ∩ memory(vm₂) = ∅
```
**Verified by**: `SystemState::verify_memory_isolation()` and enforced in all memory operations

### Invariant 2: Capability Soundness
```
action_occurs(vm, action) ↔ has_capability(vm, required_cap(action))
```
**Verified by**: Capability checks at every operation entry point

### Invariant 3: Deterministic Exit Handling
```
∀ s₁ s₂. (vmid, exit, cpu) = (vmid', exit', cpu') → handle(s₁) = handle(s₂)
```
**Verified by**: Pure functional exit handlers with no external state

### Invariant 4: Totality
```
∀ exit ∈ ExitReason. ∃ handler. handles(handler, exit)
```
**Verified by**: Exhaustive pattern matching on ExitReason enum

## Building

### Prerequisites
- Rust 1.70 or later
- Cargo

### Build Commands
```bash
cd uh-ios
cargo build --release      # Release build
cargo test                # Run tests
cargo doc --open          # Generate and view documentation
```

## Testing

The implementation includes 30+ unit tests covering:
- VM lifecycle transitions
- Memory mapping and isolation
- Capability enforcement
- Exit handler determinism and totality
- HVF interface operations

Run tests with:
```bash
cargo test
```

All tests validate that formal properties are maintained.

## Integration with DREDGE

µH-iOS serves as a root of trust for higher-level orchestration:
- **DREDGE**: Guest workload orchestration and policy definition
- **Dolly**: Verified compute task lifting between CPU and GPU contexts

This composition enables a secure, modular compute platform with formally enforced isolation guarantees.

## Safety and Security

### Trusted Computing Base (TCB)
The TCB consists of:
1. µH-iOS core (~2000 LOC Rust)
2. Apple Hypervisor.framework (assumed correct)
3. XNU kernel (assumed correct)
4. Apple Secure Boot Chain (assumed correct)

### Memory Safety
- Written in safe Rust (no unsafe code in core logic)
- Type system enforces ownership and borrowing rules
- Prevents data races and use-after-free errors

### Formal Verification
- All state transitions explicitly modeled
- Invariants checked at compile time via type system
- Runtime verification of critical properties
- Property-based testing with proptest

## Limitations

Current implementation limitations:
1. HVF bindings are stubs (not linked to actual framework)
2. No side-channel defenses
3. Limited device virtualization
4. Single-threaded execution model
5. Assumes correctness of underlying platform (XNU, HVF)

## Future Work

Planned enhancements:
1. Integration with actual Hypervisor.framework APIs
2. Machine-checked proofs in Coq or Isabelle
3. Scheduling fairness guarantees
4. Device virtualization framework
5. Side-channel mitigation strategies
6. Multi-core support
7. Integration with formally verified guest operating systems

## References

This work draws inspiration from:
- seL4: Verified microkernel
- CertiKOS: Certified concurrent OS kernel
- Komodo: Verified ARM security monitor
- Formal verification literature in systems software

## License

MIT License - See LICENSE file for details

## Contact

For questions or contributions, see the DREDGE repository:
https://github.com/QueenFi703/DREDGE
