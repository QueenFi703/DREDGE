//! Capability enforcement
//!
//! This module enforces the capability soundness invariant:
//! An action may occur if and only if the executing VM possesses
//! the corresponding capability prior to execution.

use crate::{Error, Result};
use crate::types::{SystemState, VMID, Capability};

/// Capability manager for enforcing access control
pub struct CapabilityManager;

impl CapabilityManager {
    /// Check if a VM has a specific capability
    ///
    /// Formal: capability(vm, cap) → bool
    pub fn check_capability(
        state: &SystemState,
        vmid: VMID,
        cap: Capability,
    ) -> bool {
        state.has_capability(vmid, cap)
    }
    
    /// Grant a capability to a VM
    ///
    /// Formal precondition: VM exists
    /// Formal postcondition: VM possesses capability
    pub fn grant_capability(
        state: &mut SystemState,
        vmid: VMID,
        cap: Capability,
    ) -> Result<()> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        state.grant_capability(vmid, cap);
        Ok(())
    }
    
    /// Revoke a capability from a VM
    ///
    /// Formal precondition: VM exists
    /// Formal postcondition: VM does not possess capability
    pub fn revoke_capability(
        state: &mut SystemState,
        vmid: VMID,
        cap: Capability,
    ) -> Result<()> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        if let Some(caps) = state.caps.get_mut(&vmid) {
            caps.remove(&cap);
        }
        
        Ok(())
    }
    
    /// Require a capability for an operation
    ///
    /// This is a helper function that checks for a capability
    /// and returns an error if not present.
    ///
    /// Formal: require(vm, cap) → Result<()>
    ///   where Ok(()) iff capability(vm, cap)
    pub fn require_capability(
        state: &SystemState,
        vmid: VMID,
        cap: Capability,
    ) -> Result<()> {
        if !state.has_capability(vmid, cap) {
            return Err(Error::CapabilityError(format!(
                "VM {:?} lacks required capability {:?}",
                vmid, cap
            )));
        }
        Ok(())
    }
    
    /// Get all capabilities possessed by a VM
    pub fn get_capabilities(
        state: &SystemState,
        vmid: VMID,
    ) -> Result<Vec<Capability>> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        let caps = state.caps
            .get(&vmid)
            .map(|set| set.iter().copied().collect())
            .unwrap_or_default();
        
        Ok(caps)
    }
    
    /// Transfer a capability from one VM to another
    ///
    /// Formal precondition: source VM exists, target VM exists, source has capability
    /// Formal postcondition: target has capability, source may or may not retain it (based on move parameter)
    pub fn transfer_capability(
        state: &mut SystemState,
        source_vmid: VMID,
        target_vmid: VMID,
        cap: Capability,
        move_capability: bool,
    ) -> Result<()> {
        // Verify both VMs exist
        if !state.vms.contains_key(&source_vmid) {
            return Err(Error::VMNotFound(source_vmid));
        }
        if !state.vms.contains_key(&target_vmid) {
            return Err(Error::VMNotFound(target_vmid));
        }
        
        // Verify source has capability
        if !state.has_capability(source_vmid, cap) {
            return Err(Error::CapabilityError(format!(
                "Source VM {:?} does not have capability {:?}",
                source_vmid, cap
            )));
        }
        
        // Grant to target
        state.grant_capability(target_vmid, cap);
        
        // Optionally remove from source (move semantics)
        if move_capability {
            if let Some(caps) = state.caps.get_mut(&source_vmid) {
                caps.remove(&cap);
            }
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::vm::VMManager;

    #[test]
    fn test_capability_check() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        // VM should have Execute capability after creation
        assert!(CapabilityManager::check_capability(&state, vmid, Capability::Execute));
    }

    #[test]
    fn test_capability_grant() {
        let mut state = SystemState::new();
        let vmid = state.allocate_vmid();
        state.vms.insert(vmid, crate::types::VMState::Created);
        
        assert!(!CapabilityManager::check_capability(&state, vmid, Capability::Execute));
        
        CapabilityManager::grant_capability(&mut state, vmid, Capability::Execute).unwrap();
        
        assert!(CapabilityManager::check_capability(&state, vmid, Capability::Execute));
    }

    #[test]
    fn test_capability_revoke() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        assert!(CapabilityManager::check_capability(&state, vmid, Capability::Execute));
        
        CapabilityManager::revoke_capability(&mut state, vmid, Capability::Execute).unwrap();
        
        assert!(!CapabilityManager::check_capability(&state, vmid, Capability::Execute));
    }

    #[test]
    fn test_require_capability() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        // Should succeed with capability
        assert!(CapabilityManager::require_capability(&state, vmid, Capability::Execute).is_ok());
        
        CapabilityManager::revoke_capability(&mut state, vmid, Capability::Execute).unwrap();
        
        // Should fail without capability
        assert!(CapabilityManager::require_capability(&state, vmid, Capability::Execute).is_err());
    }

    #[test]
    fn test_get_capabilities() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let caps = CapabilityManager::get_capabilities(&state, vmid).unwrap();
        
        // VM should have all basic capabilities after creation
        assert!(caps.contains(&Capability::Execute));
        assert!(caps.contains(&Capability::MapMemory));
    }

    #[test]
    fn test_capability_transfer() {
        let mut state = SystemState::new();
        let vm1 = VMManager::create_vm(&mut state).unwrap();
        let vm2 = VMManager::create_vm(&mut state).unwrap();
        
        // Remove Execute from vm2
        CapabilityManager::revoke_capability(&mut state, vm2, Capability::Execute).unwrap();
        
        assert!(CapabilityManager::check_capability(&state, vm1, Capability::Execute));
        assert!(!CapabilityManager::check_capability(&state, vm2, Capability::Execute));
        
        // Transfer with copy (both should have it)
        CapabilityManager::transfer_capability(
            &mut state, vm1, vm2, Capability::Execute, false
        ).unwrap();
        
        assert!(CapabilityManager::check_capability(&state, vm1, Capability::Execute));
        assert!(CapabilityManager::check_capability(&state, vm2, Capability::Execute));
    }

    #[test]
    fn test_capability_move() {
        let mut state = SystemState::new();
        let vm1 = VMManager::create_vm(&mut state).unwrap();
        let vm2 = VMManager::create_vm(&mut state).unwrap();
        
        // Remove Halt from vm2
        CapabilityManager::revoke_capability(&mut state, vm2, Capability::Halt).unwrap();
        
        // Transfer with move (only target should have it)
        CapabilityManager::transfer_capability(
            &mut state, vm1, vm2, Capability::Halt, true
        ).unwrap();
        
        assert!(!CapabilityManager::check_capability(&state, vm1, Capability::Halt));
        assert!(CapabilityManager::check_capability(&state, vm2, Capability::Halt));
    }
}
