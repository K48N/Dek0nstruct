from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
from datetime import datetime

class JobStatus(Enum):
    """Possible states for an export job."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    """Types of background jobs supported by the application."""
    EXPORT = "export"
    SPEECH_TO_TEXT = "speech_to_text"
    SCENE_DETECTION = "scene_detection"
    SPEAKER_DIARIZATION = "speaker_diarization"
    AUDIO_ENHANCEMENT = "audio_enhancement"
    CACHE_GENERATION = "cache_generation"
    AUTO_SUMMARIZE = "auto_summarize"

@dataclass
class ExportJob:
    """Represents a background processing job."""
    job_id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    result: Optional[Any] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate the job duration in seconds if completed."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if the job has finished (successfully or not)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)