//! µH-iOS: A Formally Verified Micro-Hypervisor Nucleus for iOS
//!
//! This library provides a minimal, verifiable isolation core for iOS,
//! implementing formally proven safety properties including memory non-interference,
//! capability soundness, deterministic VM exit handling, and totality.
//!
//! # Architecture
//!
//! µH-iOS operates as a minimal isolation core running in user space,
//! backed by Apple's Hypervisor.framework. The system enforces four key
//! formal invariants:
//!
//! 1. **Memory Non-Interference**: Distinct VMs have disjoint memory regions
//! 2. **Capability Soundness**: Actions require explicit capabilities
//! 3. **Deterministic Exit Handling**: VM exits produce deterministic state transitions
//! 4. **Totality**: All VM exits are handled by defined transitions
//!
//! # Modules
//!
//! - `types`: Core type definitions and system state
//! - `vm`: Virtual machine lifecycle management
//! - `memory`: Memory mapping and isolation
//! - `capability`: Capability enforcement
//! - `exit`: VM exit dispatching and handling
//! - `hvf`: Hypervisor.framework FFI bindings

#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

pub mod types;
pub mod vm;
pub mod memory;
pub mod capability;
pub mod exit;
pub mod hvf;

pub use types::{SystemState, VMState, VMID, Capability};

/// Result type used throughout µH-iOS
pub type Result<T> = std::result::Result<T, Error>;

/// Error types for µH-iOS operations
#[derive(Debug, thiserror::Error)]
pub enum Error {
    /// VM does not exist
    #[error("VM {0} not found")]
    VMNotFound(VMID),
    
    /// VM is in an invalid state for the requested operation
    #[error("VM {0} in invalid state")]
    InvalidVMState(VMID),
    
    /// Memory operation failed
    #[error("Memory operation failed: {0}")]
    MemoryError(String),
    
    /// Capability check failed
    #[error("Capability check failed: {0}")]
    CapabilityError(String),
    
    /// VM exit handling error
    #[error("VM exit handling error: {0}")]
    ExitError(String),
    
    /// Hypervisor.framework error
    #[error("HVF error: {0}")]
    HVFError(String),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_library_loads() {
        // Basic test to ensure library compiles and loads
        assert_eq!(std::mem::size_of::<VMID>(), 4);
    }
}
