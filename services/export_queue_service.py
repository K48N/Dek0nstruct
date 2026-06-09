from typing import Dict, Optional, Callable
import os
import logging
from pathlib import Path

from models.export_job import ExportJob, JobStatus, JobType
from .base_service import Service
from .background_job_manager import BackgroundJobManager
from .service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class ExportQueueService(Service):
    """Manages video export operations in the background."""
    
    def __init__(self):
        super().__init__()
        self.job_manager = ServiceRegistry().get_service(BackgroundJobManager)
    
    def start(self) -> None:
        """Start the export queue service."""
        super().start()
        
    def stop(self) -> None:
        """Stop the export queue service."""
        super().stop()
    
    def queue_export(self, input_path: str, output_path: str, options: Dict,
                    progress_callback: Optional[Callable[[float], None]] = None) -> str:
        """Queue a new export job."""
        def export_work():
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Here you would implement the actual export logic
            # For now, we'll just create a placeholder implementation
            total_frames = 100  # This would be calculated from the actual video
            for i in range(total_frames):
                if progress_callback:
                    progress = (i + 1) / total_frames
                    progress_callback(progress)
                # Actual export work would happen here
            
            return output_path
        
        # Submit the export job to the background job manager
        job_id = self.job_manager.submit_job(
            job_type=JobType.EXPORT,
            work_fn=export_work,
            priority=1  # Exports get high priority
        )
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[ExportJob]:
        """Get the status of an export job."""
        return self.job_manager.get_job(job_id)
    
    def get_all_jobs(self) -> list[ExportJob]:
        """Get all export jobs."""
        return [job for job in self.job_manager.get_all_jobs()
                if job.job_type == JobType.EXPORT]