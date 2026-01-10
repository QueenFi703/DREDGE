//! VM exit dispatching and handling
//!
//! This module enforces two key invariants:
//! 1. Deterministic Exit Handling: Given identical VM state and exit reason,
//!    the resulting state transition is deterministic.
//! 2. Totality: All VM exits are handled by a defined transition;
//!    no undefined behavior exists.

use crate::{Error, Result};
use crate::types::{SystemState, VMID, ExitReason, CPUState, Capability};
use crate::vm::VMManager;

/// Exit handler for processing VM exits
pub struct ExitHandler;

/// Result of handling a VM exit
#[derive(Debug, Clone)]
pub enum ExitAction {
    /// Resume VM with updated CPU state
    Resume(CPUState),
    /// Halt VM permanently
    Halt,
    /// Inject exception back to guest
    InjectException { vector: u32, cpu_state: CPUState },
}

impl ExitHandler {
    /// Process a VM exit deterministically
    ///
    /// Formal properties:
    /// 1. Totality: All exit reasons have defined handlers
    /// 2. Determinism: Same (vmid, exit_reason, cpu_state) → same ExitAction
    /// 3. Safety: Returned action maintains system invariants
    ///
    /// This is the core of the verified exit handling system.
    pub fn handle_exit(
        state: &SystemState,
        vmid: VMID,
        exit_reason: &ExitReason,
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // Verify VM exists
        if !state.vms.contains_key(&vmid) {
            return Err(Error::VMNotFound(vmid));
        }
        
        // Verify HandleExit capability
        if !state.has_capability(vmid, Capability::HandleExit) {
            return Err(Error::CapabilityError(
                "HandleExit capability required".to_string(),
            ));
        }
        
        // Dispatch based on exit reason
        // All cases are explicitly handled (totality)
        match exit_reason {
            ExitReason::Hypercall { nr, args } => {
                Self::handle_hypercall(state, vmid, *nr, args, cpu_state)
            }
            
            ExitReason::MemoryFault { gpa, write } => {
                Self::handle_memory_fault(state, vmid, *gpa, *write, cpu_state)
            }
            
            ExitReason::InstructionAbort { gpa } => {
                Self::handle_instruction_abort(state, vmid, *gpa, cpu_state)
            }
            
            ExitReason::SystemRegister { reg, write } => {
                Self::handle_system_register(state, vmid, *reg, *write, cpu_state)
            }
            
            ExitReason::WFI => {
                Self::handle_wfi(state, vmid, cpu_state)
            }
            
            ExitReason::Exception { vector } => {
                Self::handle_exception(state, vmid, *vector, cpu_state)
            }
            
            ExitReason::Cancelled => {
                Self::handle_cancelled(state, vmid, cpu_state)
            }
        }
    }
    
    /// Handle hypercall from guest
    ///
    /// Deterministic: Same hypercall number and arguments → same action
    fn handle_hypercall(
        _state: &SystemState,
        _vmid: VMID,
        nr: u64,
        _args: &[u64; 6],
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        match nr {
            // Hypercall 0: Yield (WFI-like behavior)
            0 => {
                let mut new_state = cpu_state.clone();
                new_state.pc += 4; // Advance past hypercall instruction
                Ok(ExitAction::Resume(new_state))
            }
            
            // Hypercall 1: Halt
            1 => {
                Ok(ExitAction::Halt)
            }
            
            // Unknown hypercalls: Inject undefined instruction exception
            _ => {
                Ok(ExitAction::InjectException {
                    vector: 0, // Undefined instruction
                    cpu_state: cpu_state.clone(),
                })
            }
        }
    }
    
    /// Handle memory fault
    ///
    /// Deterministic: Same GPA and access type → same action
    fn handle_memory_fault(
        _state: &SystemState,
        _vmid: VMID,
        _gpa: crate::types::GPA,
        _write: bool,
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // Memory faults are injected back to guest as data abort
        Ok(ExitAction::InjectException {
            vector: 1, // Data abort
            cpu_state: cpu_state.clone(),
        })
    }
    
    /// Handle instruction abort
    ///
    /// Deterministic: Same GPA → same action
    fn handle_instruction_abort(
        _state: &SystemState,
        _vmid: VMID,
        _gpa: crate::types::GPA,
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // Instruction aborts are injected back to guest as prefetch abort
        Ok(ExitAction::InjectException {
            vector: 2, // Prefetch abort
            cpu_state: cpu_state.clone(),
        })
    }
    
    /// Handle system register access
    ///
    /// Deterministic: Same register and access type → same action
    fn handle_system_register(
        _state: &SystemState,
        _vmid: VMID,
        _reg: u32,
        _write: bool,
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // System register accesses are emulated or trapped
        // For simplicity, we inject undefined instruction exception
        Ok(ExitAction::InjectException {
            vector: 0, // Undefined instruction
            cpu_state: cpu_state.clone(),
        })
    }
    
    /// Handle WFI (Wait For Interrupt)
    ///
    /// Deterministic: Always yields execution
    fn handle_wfi(
        _state: &SystemState,
        _vmid: VMID,
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // WFI causes VM to yield; advance PC and resume
        let mut new_state = cpu_state.clone();
        new_state.pc += 4; // Advance past WFI instruction
        Ok(ExitAction::Resume(new_state))
    }
    
    /// Handle exception from guest
    ///
    /// Deterministic: Same exception vector → same action
    fn handle_exception(
        _state: &SystemState,
        _vmid: VMID,
        vector: u32,
        cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // Guest exceptions are re-injected
        Ok(ExitAction::InjectException {
            vector,
            cpu_state: cpu_state.clone(),
        })
    }
    
    /// Handle cancelled VM
    ///
    /// Deterministic: Always halts
    fn handle_cancelled(
        _state: &SystemState,
        _vmid: VMID,
        _cpu_state: &CPUState,
    ) -> Result<ExitAction> {
        // Cancelled VMs are halted
        Ok(ExitAction::Halt)
    }
    
    /// Process the next pending exit from the queue
    ///
    /// This is the main entry point for the exit processing loop.
    pub fn process_next_exit(state: &mut SystemState) -> Result<Option<(VMID, ExitAction)>> {
        // Pop next exit from queue
        let Some((vmid, exit_reason)) = state.exits.pop_front() else {
            return Ok(None); // No pending exits
        };
        
        // Get current VM state to extract CPU state
        let vm_state = VMManager::get_vm_state(state, vmid)?;
        
        let cpu_state = match vm_state {
            crate::types::VMState::Trapped(_, cpu) => cpu.clone(),
            _ => return Err(Error::InvalidVMState(vmid)),
        };
        
        // Handle exit deterministically
        let action = Self::handle_exit(state, vmid, &exit_reason, &cpu_state)?;
        
        Ok(Some((vmid, action)))
    }
    
    /// Apply exit action to VM state
    ///
    /// This modifies the system state based on the exit action result.
    pub fn apply_exit_action(
        state: &mut SystemState,
        vmid: VMID,
        action: ExitAction,
    ) -> Result<()> {
        match action {
            ExitAction::Resume(cpu_state) => {
                VMManager::resume_vm(state, vmid, cpu_state)
            }
            
            ExitAction::Halt => {
                VMManager::halt_vm(state, vmid)
            }
            
            ExitAction::InjectException { cpu_state, .. } => {
                // For now, we resume with the CPU state
                // A full implementation would inject the exception into guest's vector table
                VMManager::resume_vm(state, vmid, cpu_state)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::vm::VMManager;

    #[test]
    fn test_exit_handler_totality() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let cpu_state = CPUState::default();
        
        // Test that all exit reasons are handled (totality)
        let exit_reasons = vec![
            ExitReason::Hypercall { nr: 0, args: [0; 6] },
            ExitReason::MemoryFault { gpa: crate::types::GPA(0x1000), write: false },
            ExitReason::InstructionAbort { gpa: crate::types::GPA(0x1000) },
            ExitReason::SystemRegister { reg: 0, write: false },
            ExitReason::WFI,
            ExitReason::Exception { vector: 0 },
            ExitReason::Cancelled,
        ];
        
        for exit_reason in exit_reasons {
            let result = ExitHandler::handle_exit(&state, vmid, &exit_reason, &cpu_state);
            assert!(result.is_ok(), "Exit reason {:?} not handled", exit_reason);
        }
    }

    #[test]
    fn test_exit_handler_determinism() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let cpu_state = CPUState::default();
        let exit_reason = ExitReason::WFI;
        
        // Call handler twice with same inputs
        let action1 = ExitHandler::handle_exit(&state, vmid, &exit_reason, &cpu_state).unwrap();
        let action2 = ExitHandler::handle_exit(&state, vmid, &exit_reason, &cpu_state).unwrap();
        
        // Results should be identical (determinism)
        match (action1, action2) {
            (ExitAction::Resume(cpu1), ExitAction::Resume(cpu2)) => {
                assert_eq!(cpu1.pc, cpu2.pc);
            }
            _ => panic!("Non-deterministic exit handling"),
        }
    }

    #[test]
    fn test_hypercall_halt() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let cpu_state = CPUState::default();
        let exit_reason = ExitReason::Hypercall { nr: 1, args: [0; 6] };
        
        let action = ExitHandler::handle_exit(&state, vmid, &exit_reason, &cpu_state).unwrap();
        
        assert!(matches!(action, ExitAction::Halt));
    }

    #[test]
    fn test_process_exit_queue() {
        let mut state = SystemState::new();
        let vmid = VMManager::create_vm(&mut state).unwrap();
        
        let cpu_state = CPUState::default();
        VMManager::initialize_vm(&mut state, vmid, cpu_state.clone()).unwrap();
        
        // Trap VM with WFI
        VMManager::trap_vm(&mut state, vmid, ExitReason::WFI, cpu_state).unwrap();
        
        // Process exit
        let result = ExitHandler::process_next_exit(&mut state).unwrap();
        assert!(result.is_some());
        
        let (exit_vmid, action) = result.unwrap();
        assert_eq!(exit_vmid, vmid);
        assert!(matches!(action, ExitAction::Resume(_)));
    }
}
