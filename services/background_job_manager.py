from typing import Dict, List, Optional, Callable
import threading
import queue
import uuid
import logging
from datetime import datetime

from models.export_job import ExportJob, JobStatus, JobType
from .base_service import Service

logger = logging.getLogger(__name__)

class BackgroundJobManager(Service):
    """Manages background processing jobs in a thread-safe manner."""
    
    def __init__(self):
        super().__init__()
        self._jobs: Dict[str, ExportJob] = {}
        self._job_queue = queue.PriorityQueue()
        self._lock = threading.Lock()
        self._worker_thread = None
        self._callbacks: Dict[str, List[Callable[[ExportJob], None]]] = {}
    
    def start(self) -> None:
        """Start the background job manager."""
        super().start()
        self._worker_thread = threading.Thread(target=self._process_jobs, daemon=True)
        self._worker_thread.start()
    
    def stop(self) -> None:
        """Stop the background job manager."""
        super().stop()
        # Add a sentinel value to stop the worker thread
        self._job_queue.put((0, None))
        if self._worker_thread:
            self._worker_thread.join()
    
    def submit_job(self, job_type: JobType, work_fn: Callable, priority: int = 1) -> str:
        """Submit a new job for background processing."""
        job_id = str(uuid.uuid4())
        job = ExportJob(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            created_at=datetime.now()
        )
        
        with self._lock:
            self._jobs[job_id] = job
        
        # Add job to queue with priority (lower number = higher priority)
        self._job_queue.put((priority, (job_id, work_fn)))
        return job_id
    
    def get_job(self, job_id: str) -> Optional[ExportJob]:
        """Get the current state of a job."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ExportJob]:
        """Get a list of all jobs."""
        with self._lock:
            return list(self._jobs.values())
    
    def register_callback(self, job_id: str, callback: Callable[[ExportJob], None]) -> None:
        """Register a callback to be called when the job status changes."""
        with self._lock:
            if job_id not in self._callbacks:
                self._callbacks[job_id] = []
            self._callbacks[job_id].append(callback)
    
    def _process_jobs(self) -> None:
        """Worker thread that processes jobs from the queue."""
        while self.is_running:
            try:
                priority, item = self._job_queue.get()
                if item is None:  # Sentinel value
                    break
                    
                job_id, work_fn = item
                job = self.get_job(job_id)
                if not job:
                    continue
                
                # Update job status
                with self._lock:
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now()
                self._notify_callbacks(job)
                
                try:
                    # Execute the job
                    result = work_fn()
                    
                    # Update job status on success
                    with self._lock:
                        job.status = JobStatus.COMPLETED
                        job.completed_at = datetime.now()
                        job.result = result
                        
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    # Update job status on failure
                    with self._lock:
                        job.status = JobStatus.FAILED
                        job.completed_at = datetime.now()
                        job.error_message = str(e)
                
                self._notify_callbacks(job)
                self._job_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in job processor: {e}")
    
    def _notify_callbacks(self, job: ExportJob) -> None:
        """Notify all registered callbacks for a job."""
        callbacks = self._callbacks.get(job.job_id, [])
        for callback in callbacks:
            try:
                callback(job)
            except Exception as e:
                logger.error(f"Error in job callback: {e}")