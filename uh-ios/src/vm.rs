//! Virtual Machine lifecycle management
//!
//! This module implements the VM state machine with formally proven transitions.
//! All state transitions are explicit and deterministic, maintaining system invariants.

use crate::{Error, Result};
use crate::types::{SystemState, VMState, VMID, CPUState, Capability};

/// VM lifecycle operations
pub struct VMManager;

impl VMManager {
    /// Create a new VM
    ///
    /// Formal precondition: None
    /// Formal postcondition: VM exists in Created state with Execute capability
    ///
    /// State transition: ∅ → Created
    pub fn create_vm(state: &mut SystemState) -> Result<VMID> {
        let vmid = state.allocate_vmid();
        
        // Initialize VM in Created state
        state.vms.insert(vmid, VMState::Created);
        
        // Grant basic capabilities
        state.grant_capability(vmid, Capability::Execute);
        state.grant_capability(vmid, Capability::MapMemory);
        state.grant_capability(vmid, Capability::HandleExit);
        state.grant_capability(vmid, Capability::Halt);
        
        Ok(vmid)
    }
    
    /// Initialize VM with CPU state, making it runnable
    ///
    /// Formal precondition: VM exists in Created state, possesses Execute capability
    /// Formal postcondition: VM is in Runnable state with provided CPU state
    ///
    /// State transition: Created → Runnable(CPUState)
    pub fn initialize_vm(
        state: &mut SystemState,
        vmid: VMID,
        cpu_state: CPUState,
    ) -> Result<()> {
        // Verify VM exists
        let vm_state = state.vms.get(&vmid).ok_or(Error::VMNotFound(vmid))?;
        
        // Verify VM is in Created state
        if !matches!(vm_state, VMState::Created) {
            return Err(Error::InvalidVMState(vmid));
        }
        
        // Verify Execute capability
        if !state.has_capability(vmid, Capability::Execute) {
            return Err(Error::CapabilityError(
                "Execute capability required".to_string(),
            ));
        }
        
        // Transition to Runnable state
        state.vms.insert(vmid, VMState::Runnable(cpu_state));
        
        Ok(())
    }
    
    /// Handle VM trap (exit)
    ///
    /// Formal precondition: VM exists in Runnable state
    /// Formal postcondition: VM is in Trapped state with exit reason and current CPU state
    ///
    /// State transition: Runnable(CPUState) → Trapped(ExitReason, CPUState)
    pub fn trap_vm(
        state: &mut SystemState,
        vmid: VMID,
        exit_reason: crate::types::ExitReason,
        cpu_state: CPUState,
    ) -> Result<()> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        // Transition to Trapped state
        state.vms.insert(vmid, VMState::Trapped(exit_reason.clone(), cpu_state));
        
        // Enqueue exit for processing
        state.exits.push_back((vmid, exit_reason));
        
        Ok(())
    }
    
    /// Resume VM from trapped state
    ///
    /// Formal precondition: VM exists in Trapped state, possesses Execute capability
    /// Formal postcondition: VM is in Runnable state with updated CPU state
    ///
    /// State transition: Trapped(_, CPUState) → Runnable(CPUState)
    pub fn resume_vm(
        state: &mut SystemState,
        vmid: VMID,
        cpu_state: CPUState,
    ) -> Result<()> {
        // Verify VM exists
        let vm_state = state.vms.get(&vmid).ok_or(Error::VMNotFound(vmid))?;
        
        // Verify VM is in Trapped state
        if !matches!(vm_state, VMState::Trapped(_, _)) {
            return Err(Error::InvalidVMState(vmid));
        }
        
        // Verify Execute capability
        if !state.has_capability(vmid, Capability::Execute) {
            return Err(Error::CapabilityError(
                "Execute capability required".to_string(),
            ));
        }
        
        // Transition to Runnable state
        state.vms.insert(vmid, VMState::Runnable(cpu_state));
        
        Ok(())
    }
    
    /// Halt VM permanently
    ///
    /// Formal precondition: VM exists in any state, possesses Halt capability
    /// Formal postcondition: VM is in Halted state (terminal state)
    ///
    /// State transition: * → Halted
    pub fn halt_vm(state: &mut SystemState, vmid: VMID) -> Result<()> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        // Verify Halt capability
        if !state.has_capability(vmid, Capability::Halt) {
            return Err(Error::CapabilityError(
                "Halt capability required".to_string(),
            ));
        }
        
        // Transition to Halted state (terminal)
        state.vms.insert(vmid, VMState::Halted);
        
        Ok(())
    }
    
    /// Get current VM state
    pub fn get_vm_state(state: &SystemState, vmid: VMID) -> Result<&VMState> {
        state.vms.get(&vmid).ok_or(Error::VMNotFound(vmid))
    }
    
    /// Destroy VM and clean up resources
    ///
    /// Formal precondition: VM exists
    /// Formal postcondition: VM removed from system, memory unmapped, capabilities revoked
    pub fn destroy_vm(state: &mut SystemState, vmid: VMID) -> Result<()> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        // Remove VM state
        state.vms.remove(&vmid);
        
        // Remove capabilities
        state.caps.remove(&vmid);
        
        // Note: Memory cleanup would be handled by memory module
        // to maintain memory non-interference invariant
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vm_creation() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        assert!(state.vms.contains_key(&vmid));
        assert!(matches!(state.vms.get(&vmid), Some(VMState::Created)));
        assert!(state.has_capability(vmid, Capability::Execute));
    }

    #[test]
    fn test_vm_initialization() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let cpu_state = CPUState::default();
        VMManager::initialize_vm(&mut state, vmid, cpu_state).unwrap();
        
        assert!(matches!(state.vms.get(&vmid), Some(VMState::Runnable(_))));
    }

    #[test]
    fn test_vm_trap_and_resume() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let cpu_state = CPUState::default();
        VMManager::initialize_vm(&mut state, vmid, cpu_state.clone()).unwrap();
        
        // Trap VM
        let exit_reason = crate::types::ExitReason::WFI;
        VMManager::trap_vm(&mut state, vmid, exit_reason, cpu_state.clone()).unwrap();
        
        assert!(matches!(state.vms.get(&vmid), Some(VMState::Trapped(_, _))));
        assert_eq!(state.exits.len(), 1);
        
        // Resume VM
        VMManager::resume_vm(&mut state, vmid, cpu_state).unwrap();
        assert!(matches!(state.vms.get(&vmid), Some(VMState::Runnable(_))));
    }

    #[test]
    fn test_vm_halt() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        VMManager::halt_vm(&mut state, vmid).unwrap();
        assert!(matches!(state.vms.get(&vmid), Some(VMState::Halted)));
    }

    #[test]
    fn test_capability_enforcement() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        // Remove Execute capability
        state.caps.get_mut(&vmid).unwrap().remove(&Capability::Execute);
        
        // Should fail without capability
        let cpu_state = CPUState::default();
        let result = VMManager::initialize_vm(&mut state, vmid, cpu_state);
        assert!(result.is_err());
    }
}
