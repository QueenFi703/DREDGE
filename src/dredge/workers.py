"""
DREDGE Distributed Workers and Queue Infrastructure
Provides scale-out capabilities with task queues and worker processes.
"""
import json
import time
import logging
import uuid
from typing import Dict, Any, Optional, Callable, List
from queue import Queue, Empty
from threading import Thread, Event
import hashlib

logger = logging.getLogger("DREDGE.Workers")


class Task:
    """Represents a task to be executed by a worker."""
    
    def __init__(self, task_id: str, operation: str, params: Dict[str, Any], 
                 callback: Optional[Callable] = None):
        self.task_id = task_id
        self.operation = operation
        self.params = params
        self.callback = callback
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.status = 'pending'  # pending, running, completed, failed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'task_id': self.task_id,
            'operation': self.operation,
            'params': self.params,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'status': self.status,
            'duration': self.completed_at - self.started_at if self.completed_at and self.started_at else None,
            'result': self.result,
            'error': self.error
        }


class TaskQueue:
    """Thread-safe task queue for distributing work to workers."""
    
    def __init__(self, maxsize: int = 0):
        """
        Initialize task queue.
        
        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        self._queue = Queue(maxsize=maxsize)
        self._results: Dict[str, Task] = {}
        self._stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        logger.info(f"Initialized TaskQueue with maxsize={maxsize}")
    
    def submit(self, operation: str, params: Dict[str, Any], 
               task_id: Optional[str] = None) -> str:
        """
        Submit a task to the queue.
        
        Args:
            operation: Operation name
            params: Operation parameters
            task_id: Optional task ID (auto-generated if not provided)
            
        Returns:
            Task ID
        """
        if not task_id:
            # Generate cryptographically secure task ID
            unique_part = uuid.uuid4().hex[:12]
            task_id = f"{operation}_{unique_part}"
        
        task = Task(task_id, operation, params)
        self._queue.put(task)
        self._results[task_id] = task
        self._stats['tasks_submitted'] += 1
        
        logger.info(f"Task submitted: {task_id} (operation={operation})")
        return task_id
    
    def get_task(self, timeout: Optional[float] = None) -> Optional[Task]:
        """
        Get next task from queue.
        
        Args:
            timeout: Timeout in seconds (None = block forever)
            
        Returns:
            Task or None if timeout
        """
        try:
            task = self._queue.get(timeout=timeout)
            task.status = 'running'
            task.started_at = time.time()
            return task
        except Empty:
            return None
    
    def complete_task(self, task: Task, result: Dict[str, Any]):
        """Mark task as completed with result."""
        task.status = 'completed'
        task.result = result
        task.completed_at = time.time()
        self._stats['tasks_completed'] += 1
        self._queue.task_done()
        logger.info(f"Task completed: {task.task_id}")
    
    def fail_task(self, task: Task, error: str):
        """Mark task as failed with error."""
        task.status = 'failed'
        task.error = error
        task.completed_at = time.time()
        self._stats['tasks_failed'] += 1
        self._queue.task_done()
        logger.error(f"Task failed: {task.task_id} - {error}")
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result for a task."""
        if task_id in self._results:
            return self._results[task_id].to_dict()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self._stats,
            'queue_size': self._queue.qsize(),
            'pending_results': len(self._results)
        }


class Worker:
    """Worker process that executes tasks from a queue."""
    
    def __init__(self, worker_id: str, task_queue: TaskQueue, 
                 executor: Callable[[str, Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize worker.
        
        Args:
            worker_id: Unique worker identifier
            task_queue: Task queue to pull from
            executor: Function that executes tasks (operation, params) -> result
        """
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.executor = executor
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._stats = {
            'tasks_executed': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        logger.info(f"Initialized worker: {worker_id}")
    
    def start(self):
        """Start the worker thread."""
        if self._thread and self._thread.is_alive():
            logger.warning(f"Worker {self.worker_id} already running")
            return
        
        self._stop_event.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Worker started: {self.worker_id}")
    
    def stop(self, timeout: float = 5.0):
        """
        Stop the worker thread.
        
        Args:
            timeout: Maximum time to wait for worker to stop
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info(f"Worker stopped: {self.worker_id}")
    
    def _run(self):
        """Main worker loop."""
        logger.info(f"Worker {self.worker_id} starting execution loop")
        
        while not self._stop_event.is_set():
            try:
                # Get task with timeout so we can check stop event
                task = self.task_queue.get_task(timeout=1.0)
                
                if task is None:
                    continue
                
                logger.debug(f"Worker {self.worker_id} executing task: {task.task_id}")
                start_time = time.time()
                
                try:
                    # Execute task
                    result = self.executor(task.operation, task.params)
                    self.task_queue.complete_task(task, result)
                    
                    # Update stats
                    self._stats['tasks_succeeded'] += 1
                    self._stats['tasks_executed'] += 1
                    self._stats['total_execution_time'] += time.time() - start_time
                    
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} task execution failed: {e}", exc_info=True)
                    self.task_queue.fail_task(task, str(e))
                    self._stats['tasks_failed'] += 1
                    self._stats['tasks_executed'] += 1
                
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
        
        logger.info(f"Worker {self.worker_id} exiting execution loop")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return {
            'worker_id': self.worker_id,
            'is_alive': self._thread.is_alive() if self._thread else False,
            **self._stats
        }


class WorkerPool:
    """Pool of workers for parallel task execution."""
    
    def __init__(self, num_workers: int, executor: Callable[[str, Dict[str, Any]], Dict[str, Any]]):
        """
        Initialize worker pool.
        
        Args:
            num_workers: Number of workers to create
            executor: Function that executes tasks
        """
        self.task_queue = TaskQueue()
        self.workers: List[Worker] = []
        
        for i in range(num_workers):
            worker = Worker(f"worker_{i}", self.task_queue, executor)
            self.workers.append(worker)
        
        logger.info(f"Initialized WorkerPool with {num_workers} workers")
    
    def start(self):
        """Start all workers."""
        for worker in self.workers:
            worker.start()
        logger.info(f"Started {len(self.workers)} workers")
    
    def stop(self, timeout: float = 5.0):
        """Stop all workers."""
        for worker in self.workers:
            worker.stop(timeout=timeout)
        logger.info(f"Stopped {len(self.workers)} workers")
    
    def submit(self, operation: str, params: Dict[str, Any]) -> str:
        """Submit a task to the pool."""
        return self.task_queue.submit(operation, params)
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result for a task."""
        return self.task_queue.get_result(task_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        worker_stats = [w.get_stats() for w in self.workers]
        queue_stats = self.task_queue.get_stats()
        
        return {
            'num_workers': len(self.workers),
            'workers': worker_stats,
            'queue': queue_stats,
            'total_tasks_executed': sum(w['tasks_executed'] for w in worker_stats),
            'total_tasks_succeeded': sum(w['tasks_succeeded'] for w in worker_stats),
            'total_tasks_failed': sum(w['tasks_failed'] for w in worker_stats)
        }
