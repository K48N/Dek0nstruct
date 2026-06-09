"""
High-level video processing engine
"""
import os
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.segment import Segment
from utils.ffmpeg_wrapper import FFmpegWrapper


@dataclass
class ProcessingOptions:
    """Options for video processing"""
    # Basic options
    output_format: str = 'mp4'
    parallel_processing: bool = True
    max_workers: int = 4
    export_both_formats: bool = True  # Export both video and audio if segment requests one
    
    # Performance options
    use_gpu: bool = True
    codec_copy: bool = True
    
    # Video settings
    video_codec: str = 'h264'
    video_bitrate: Optional[str] = None
    video_preset: str = 'medium'  # ultrafast to veryslow
    video_crf: int = 23  # 0-51, lower is better quality
    video_pixel_format: str = 'yuv420p'
    width: Optional[int] = None  # If None, maintain source
    height: Optional[int] = None
    fps: Optional[float] = None
    maintain_aspect_ratio: bool = True
    
    # Audio settings
    audio_codec: str = 'aac'
    audio_bitrate: Optional[str] = None
    audio_sample_rate: int = 44100
    audio_channels: Optional[str] = None  # mono, stereo, None for source
    normalize_audio: bool = False
    mp3_quality: int = 2  # Legacy option for MP3 export
    
    # Additional settings
    metadata: Dict[str, str] = None
    extra_args: List[str] = None
    
    def __post_init__(self):
        """Initialize optional fields"""
        if self.metadata is None:
            self.metadata = {}
        if self.extra_args is None:
            self.extra_args = []


@dataclass
class ProcessingResult:
    """Result of processing a segment"""
    segment: Segment
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0


class VideoEngine:
    """Main video processing engine"""
    
    def __init__(self):
        self.ffmpeg = FFmpegWrapper()
        self.current_video: Optional[str] = None
        self.video_info: Optional[Dict[str, Any]] = None
        self._progress_callback: Optional[Callable] = None
        self._cancel_requested = False
    
    def load_video(self, file_path: str) -> Dict[str, Any]:
        """
        Load video and get information
        
        Returns:
            Video information dictionary
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        self.current_video = file_path
        self.video_info = self.ffmpeg.get_video_info(file_path)
        return self.video_info
    
    def validate_segments(self, segments: List[Segment]) -> List[str]:
        """
        Validate segments against current video
        
        Returns:
            List of validation errors (empty if valid)
        """
        if not self.current_video or not self.video_info:
            return ["No video loaded"]
        
        errors = []
        duration = self.video_info['duration']
        
        for i, segment in enumerate(segments):
            # Check individual segment validity
            try:
                segment.validate()
            except ValueError as e:
                errors.append(f"Segment {i+1} ({segment.label}): {str(e)}")
            
            # Check against video duration
            if segment.end > duration:
                errors.append(
                    f"Segment {i+1} ({segment.label}): "
                    f"End time {segment.end:.2f}s exceeds video duration {duration:.2f}s"
                )
            
            # Check for overlaps
            for j, other in enumerate(segments[i+1:], start=i+1):
                if segment.overlaps_with(other):
                    errors.append(
                        f"Segments {i+1} and {j+1} overlap: "
                        f"'{segment.label}' and '{other.label}'"
                    )
        
        return errors
    
    def process_segments(
        self,
        segments: List[Segment],
        output_dir: str,
        options: ProcessingOptions,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[ProcessingResult]:
        """
        Process all segments
        
        Args:
            segments: List of segments to process
            output_dir: Output directory
            options: Processing options
            progress_callback: Callback(current, total, message)
        
        Returns:
            List of processing results
        """
        if not self.current_video:
            raise RuntimeError("No video loaded")
        
        # Validate first
        errors = self.validate_segments(segments)
        if errors:
            raise ValueError(f"Validation failed:\n" + "\n".join(errors))
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        self._progress_callback = progress_callback
        self._cancel_requested = False
        
        results = []
        
        if options.parallel_processing and len(segments) > 1:
            results = self._process_parallel(segments, output_dir, options)
        else:
            results = self._process_sequential(segments, output_dir, options)
        
        return results
    
    def _process_sequential(
        self,
        segments: List[Segment],
        output_dir: str,
        options: ProcessingOptions
    ) -> List[ProcessingResult]:
        """Process segments sequentially"""
        results = []
        total = len(segments)
        
        for i, segment in enumerate(segments, 1):
            if self._cancel_requested:
                break
            
            if self._progress_callback:
                self._progress_callback(i, total, f"Processing: {segment.label}")
            
            result = self._process_single_segment(segment, output_dir, options)
            results.append(result)
        
        return results
    
    def _process_parallel(
        self,
        segments: List[Segment],
        output_dir: str,
        options: ProcessingOptions
    ) -> List[ProcessingResult]:
        """Process segments in parallel"""
        results = []
        total = len(segments)
        completed = 0
        
        with ThreadPoolExecutor(max_workers=options.max_workers) as executor:
            # Submit all tasks
            future_to_segment = {
                executor.submit(
                    self._process_single_segment,
                    segment,
                    output_dir,
                    options
                ): segment
                for segment in segments
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_segment):
                if self._cancel_requested:
                    executor.shutdown(wait=False)
                    break
                
                result = future.result()
                results.append(result)
                
                completed += 1
                if self._progress_callback:
                    self._progress_callback(
                        completed,
                        total,
                        f"Completed: {result.segment.label}"
                    )
        
        # Sort results by original segment order
        segment_order = {id(s): i for i, s in enumerate(segments)}
        results.sort(key=lambda r: segment_order.get(id(r.segment), 0))
        
        return results
    
    def _process_single_segment(
        self,
        segment: Segment,
        output_dir: str,
        options: ProcessingOptions
    ) -> ProcessingResult:
        """Process a single segment"""
        import time
        start_time = time.time()
        
        try:
            # Sanitize filename
            safe_label = self._sanitize_filename(segment.label)
            base_name = f"{safe_label}_{int(segment.start)}_{int(segment.end)}"
            
            # Export video if requested
            if segment.export_video:
                video_path = os.path.join(
                    output_dir,
                    f"{base_name}.{options.output_format}"
                )
                
                # Extract video with full processing options
                self.ffmpeg.extract_clip(
                    self.current_video,
                    video_path,
                    segment.start,
                    segment.end,
                    options
                )
            
            # Export audio if requested OR if export_both_formats is enabled
            if segment.export_audio or options.export_both_formats:
                audio_path = os.path.join(output_dir, f"{base_name}.mp3")
                
                # For audio-only export, create optimized MP3 options
                audio_options = ProcessingOptions(
                    output_format="mp3",
                    codec_copy=False,
                    video_codec=None,
                    audio_codec="libmp3lame",
                    audio_channels=options.audio_channels,
                    audio_sample_rate=options.audio_sample_rate,
                    normalize_audio=options.normalize_audio,
                    mp3_quality=options.mp3_quality,
                    extra_args=["-q:a", str(options.mp3_quality)]  # Variable bitrate quality
                )
                
                self.ffmpeg.extract_clip(
                    self.current_video,
                    audio_path,
                    segment.start,
                    segment.end,
                    audio_options
                )
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                segment=segment,
                success=True,
                output_path=output_dir,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                segment=segment,
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename by removing invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def cancel_processing(self) -> None:
        """Request cancellation of current processing"""
        self._cancel_requested = True
    
    def generate_waveform(self, output_path: str) -> bool:
        """Generate waveform for current video"""
        if not self.current_video:
            return False
        
        return self.ffmpeg.generate_waveform(self.current_video, output_path)
    
    def generate_thumbnail(
        self,
        time_position: float,
        output_path: str,
        width: int = 320,
        height: int = 180
    ) -> bool:
        """Generate thumbnail at specific time"""
        if not self.current_video:
            return False
        
        return self.ffmpeg.generate_thumbnail(
            self.current_video,
            output_path,
            time_position,
            width,
            height
        )
    
    def get_gpu_info(self) -> Dict[str, bool]:
        """Get available GPU acceleration"""
        return self.ffmpeg.gpu_available