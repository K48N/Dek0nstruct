"""
Batch processing for multiple videos
"""
import os
from pathlib import Path
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.segment import Segment
from core.video_engine import VideoEngine, ProcessingOptions, ProcessingResult


@dataclass
class BatchJob:
    """Represents a batch processing job"""
    video_path: str
    segments: List[Segment]
    output_dir: str
    status: str = "pending"  # pending, processing, complete, failed
    error: Optional[str] = None
    results: List[ProcessingResult] = None


class BatchProcessor:
    """Process multiple videos with same segment configuration"""
    
    def __init__(self):
        self.engine = VideoEngine()
        self.jobs: List[BatchJob] = []
        self._cancel_requested = False
    
    def add_job(self, video_path: str, segments: List[Segment], output_dir: str):
        """Add a job to the batch"""
        job = BatchJob(
            video_path=video_path,
            segments=segments.copy(),
            output_dir=output_dir
        )
        self.jobs.append(job)
    
    def clear_jobs(self):
        """Clear all jobs"""
        self.jobs.clear()
    
    def process_all(
        self,
        options: ProcessingOptions,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List['BatchJob']:
        total = len(self.jobs)
        for i, job in enumerate(self.jobs, 1):
            if self._cancel_requested:
                break
            if progress_callback:
                progress_callback(i, total, f"Processing: {Path(job.video_path).name}")
            try:
                job.status = "processing"
                self.engine.load_video(job.video_path)
                adjusted_segments = self._adjust_segments_to_video(
                    job.segments, self.engine.video_info['duration']
                )
                job.results = self.engine.process_segments(
                    adjusted_segments, job.output_dir, options
                )
                job.status = "complete"
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
        return self.jobs
    
    def _adjust_segments_to_video(
        self,
        segments: List[Segment],
        video_duration: float
    ) -> List[Segment]:
        """
        Adjust segments to fit within video duration
        
        If segments exceed duration, they are scaled proportionally
        """
        if not segments:
            return []
        
        max_end = max(s.end for s in segments)
        
        if max_end <= video_duration:
            return segments
        
        # Scale segments to fit
        scale = video_duration / max_end
        adjusted = []
        
        for seg in segments:
            adjusted.append(Segment(
                start=seg.start * scale,
                end=seg.end * scale,
                label=seg.label,
                color=seg.color,
                export_video=seg.export_video,
                export_audio=seg.export_audio
            ))
        
        return adjusted
    
    def cancel(self):
        """Cancel batch processing"""
        self._cancel_requested = True
        self.engine.cancel_processing()
    
    def get_summary(self) -> Dict:
        """Get batch processing summary"""
        total = len(self.jobs)
        complete = sum(1 for j in self.jobs if j.status == "complete")
        failed = sum(1 for j in self.jobs if j.status == "failed")
        pending = sum(1 for j in self.jobs if j.status == "pending")
        
        return {
            'total': total,
            'complete': complete,
            'failed': failed,
            'pending': pending
        }