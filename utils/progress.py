"""Progress reporting system for background tasks."""
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time

class ProgressState(Enum):
    """States for a progress operation."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressInfo:
    """Information about an operation's progress."""
    operation_id: str
    state: ProgressState
    progress: float  # 0.0 to 1.0
    message: str
    current_step: int
    total_steps: int
    start_time: float
    update_time: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.state == ProgressState.NOT_STARTED:
            return 0.0
        end_time = time.time() if self.state == ProgressState.RUNNING else self.update_time
        return end_time - self.start_time

    @property
    def estimated_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if self.state != ProgressState.RUNNING or self.progress <= 0:
            return None
        elapsed = self.elapsed_time
        return (elapsed / self.progress) - elapsed

class ProgressReporter:
    """Handles progress reporting for long-running operations."""
    
    def __init__(self, operation_id: str, total_steps: int = 100,
                 callback: Optional[Callable[[ProgressInfo], None]] = None):
        self.operation_id = operation_id
        self.total_steps = total_steps
        self.callback = callback
        self.current_step = 0
        self.start_time = time.time()
        self.state = ProgressState.NOT_STARTED
        self.message = ""
        self.error = None
        self.details = {}
    
    def start(self, message: str = "Starting..."):
        """Start the operation."""
        self.state = ProgressState.RUNNING
        self.message = message
        self.start_time = time.time()
        self._notify()
    
    def update(self, step: int, message: str, **details):
        """Update progress."""
        self.current_step = min(step, self.total_steps)
        self.message = message
        self.details.update(details)
        self._notify()
    
    def increment(self, amount: int = 1, message: Optional[str] = None):
        """Increment progress by a number of steps."""
        self.update(
            self.current_step + amount,
            message or self.message
        )
    
    def pause(self, message: str = "Paused"):
        """Pause the operation."""
        self.state = ProgressState.PAUSED
        self.message = message
        self._notify()
    
    def resume(self, message: str = "Resumed"):
        """Resume the operation."""
        self.state = ProgressState.RUNNING
        self.message = message
        self._notify()
    
    def complete(self, message: str = "Completed"):
        """Mark the operation as completed."""
        self.current_step = self.total_steps
        self.state = ProgressState.COMPLETED
        self.message = message
        self._notify()
    
    def fail(self, error: str):
        """Mark the operation as failed."""
        self.state = ProgressState.FAILED
        self.error = error
        self.message = f"Failed: {error}"
        self._notify()
    
    def cancel(self, message: str = "Cancelled"):
        """Mark the operation as cancelled."""
        self.state = ProgressState.CANCELLED
        self.message = message
        self._notify()
    
    def _notify(self):
        """Notify callback of progress update."""
        if self.callback:
            info = ProgressInfo(
                operation_id=self.operation_id,
                state=self.state,
                progress=self.current_step / self.total_steps,
                message=self.message,
                current_step=self.current_step,
                total_steps=self.total_steps,
                start_time=self.start_time,
                update_time=time.time(),
                error=self.error,
                details=self.details.copy()
            )
            self.callback(info)