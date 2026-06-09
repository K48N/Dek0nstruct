from typing import Optional, Dict, List
import os
import json
import logging
from pathlib import Path
import shutil
import hashlib
from datetime import datetime, timedelta

from models.export_job import JobType
from .base_service import Service
from .background_job_manager import BackgroundJobManager
from .service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class MediaCache:
    """Represents cached media data."""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load cache index
        self.index_path = self.cache_dir / "cache_index.json"
        self.index: Dict[str, Dict] = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict]:
        """Load the cache index file."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
        return {}
    
    def _save_index(self):
        """Save the cache index file."""
        with open(self.index_path, "w") as f:
            json.dump(self.index, f, indent=2)
    
    def get_cache_path(self, media_path: str, cache_type: str) -> Path:
        """Get the path for a cached item."""
        media_hash = hashlib.md5(media_path.encode()).hexdigest()
        return self.cache_dir / cache_type / media_hash
    
    def has_cache(self, media_path: str, cache_type: str) -> bool:
        """Check if media has cached data."""
        cache_path = self.get_cache_path(media_path, cache_type)
        return cache_path.exists()
    
    def get_cache_info(self, media_path: str) -> Optional[Dict]:
        """Get cache information for a media file."""
        media_hash = hashlib.md5(media_path.encode()).hexdigest()
        return self.index.get(media_hash)
    
    def add_cache_entry(self, media_path: str, cache_type: str,
                      cache_path: Path, metadata: Optional[Dict] = None):
        """Add a new cache entry."""
        media_hash = hashlib.md5(media_path.encode()).hexdigest()
        
        if media_hash not in self.index:
            self.index[media_hash] = {
                "media_path": media_path,
                "cache_types": {},
                "last_accessed": datetime.now().isoformat()
            }
        
        self.index[media_hash]["cache_types"][cache_type] = {
            "path": str(cache_path),
            "created": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self._save_index()
    
    def remove_cache(self, media_path: str, cache_type: Optional[str] = None):
        """Remove cached data for a media file."""
        media_hash = hashlib.md5(media_path.encode()).hexdigest()
        
        if media_hash in self.index:
            if cache_type:
                # Remove specific cache type
                if cache_type in self.index[media_hash]["cache_types"]:
                    cache_path = Path(self.index[media_hash]["cache_types"][cache_type]["path"])
                    if cache_path.exists():
                        if cache_path.is_file():
                            cache_path.unlink()
                        else:
                            shutil.rmtree(cache_path)
                    del self.index[media_hash]["cache_types"][cache_type]
            else:
                # Remove all cache types
                for cache_info in self.index[media_hash]["cache_types"].values():
                    cache_path = Path(cache_info["path"])
                    if cache_path.exists():
                        if cache_path.is_file():
                            cache_path.unlink()
                        else:
                            shutil.rmtree(cache_path)
                del self.index[media_hash]
            
            self._save_index()
    
    def cleanup_old_cache(self, max_age: timedelta):
        """Remove cache entries older than max_age."""
        now = datetime.now()
        to_remove = []
        
        for media_hash, cache_info in self.index.items():
            last_accessed = datetime.fromisoformat(cache_info["last_accessed"])
            if now - last_accessed > max_age:
                to_remove.append(media_hash)
        
        for media_hash in to_remove:
            self.remove_cache(self.index[media_hash]["media_path"])

class MediaCacheService(Service):
    """Service for managing media cache (proxies, waveforms, thumbnails)."""
    
    CACHE_TYPES = {
        "proxy": ".mp4",
        "waveform": ".json",
        "thumbnails": "",  # Directory of images
        "preview": ".mp4"
    }
    
    def __init__(self):
        super().__init__()
        self.job_manager = ServiceRegistry().get_service(BackgroundJobManager)
        self.cache = None
        self._cache_dir = None
    
    def start(self) -> None:
        """Start the media cache service."""
        super().start()
        
        # Initialize cache in user's app data directory
        app_data = os.getenv("APPDATA") or os.path.expanduser("~/.local/share")
        self._cache_dir = os.path.join(app_data, "Dek0nstruct", "cache")
        self.cache = MediaCache(self._cache_dir)
        
        # Clean up old cache entries (older than 30 days)
        self.cache.cleanup_old_cache(timedelta(days=30))
    
    def stop(self) -> None:
        """Stop the media cache service."""
        super().stop()
        self.cache = None
    
    def generate_proxy(self, media_path: str) -> str:
        """Queue proxy generation for a media file."""
        def work_fn():
            from utils.ffmpeg_wrapper import FFmpegWrapper
            ffmpeg = FFmpegWrapper()
            
            cache_path = self.cache.get_cache_path(media_path, "proxy")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate low-resolution proxy
            try:
                from core.video_engine import ProcessingOptions
                options = ProcessingOptions(
                    width=640,  # Low-res proxy
                    maintain_aspect_ratio=True,
                    video_codec='h264',
                    video_preset='fast',
                    video_crf=28,  # Lower quality for proxy
                    audio_codec='aac',
                    audio_bitrate='96k',
                    use_gpu=True  # Enable GPU acceleration
                )
                
                video_info = ffmpeg.get_video_info(media_path)
                ffmpeg.extract_clip(
                    media_path,
                    str(cache_path),
                    0,  # Start from beginning
                    video_info['duration'],
                    options
                )
                
                self.cache.add_cache_entry(
                    media_path,
                    "proxy",
                    cache_path,
                    {"width": 640}
                )
                return str(cache_path)
            except Exception as e:
                logger.error(f"Failed to generate proxy: {e}")
                if cache_path.exists():
                    cache_path.unlink()
                return None
            
        return self.job_manager.submit_job(
            job_type=JobType.CACHE_GENERATION,
            work_fn=work_fn
        )
    
    def generate_waveform(self, media_path: str) -> str:
        """Queue waveform generation for a media file."""
        def work_fn():
            from utils.ffmpeg_wrapper import FFmpegWrapper
            ffmpeg = FFmpegWrapper()
            
            cache_path = self.cache.get_cache_path(media_path, "waveform")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate waveform visualization
            try:
                if ffmpeg.generate_waveform(
                    media_path,
                    str(cache_path.with_suffix('.png')),  # Store as PNG
                    width=1200,
                    height=100
                ):
                    self.cache.add_cache_entry(
                        media_path,
                        "waveform",
                        cache_path.with_suffix('.png'),
                        {"width": 1200, "height": 100}
                    )
                    return str(cache_path.with_suffix('.png'))
                return None
            except Exception as e:
                logger.error(f"Failed to generate waveform: {e}")
                wave_path = cache_path.with_suffix('.png')
                if wave_path.exists():
                    wave_path.unlink()
                return None
            
        return self.job_manager.submit_job(
            job_type=JobType.CACHE_GENERATION,
            work_fn=work_fn
        )
    
    def generate_thumbnails(self, media_path: str, interval: float = 1.0) -> str:
        """Queue thumbnail generation for a media file."""
        def work_fn():
            from utils.ffmpeg_wrapper import FFmpegWrapper
            ffmpeg = FFmpegWrapper()
            
            cache_path = self.cache.get_cache_path(media_path, "thumbnails")
            cache_path.mkdir(parents=True, exist_ok=True)
            
            try:
                # Get video duration
                video_info = ffmpeg.get_video_info(media_path)
                duration = video_info['duration']
                
                # Generate thumbnails at regular intervals
                positions = []
                current_time = 0
                while current_time < duration:
                    # Generate individual thumbnail
                    thumb_path = cache_path / f"thumb_{int(current_time*10):05d}.jpg"
                    if ffmpeg.generate_thumbnail(
                        media_path,
                        str(thumb_path),
                        current_time,
                        width=160,
                        height=90
                    ):
                        positions.append(current_time)
                    current_time += interval
                
                if positions:
                    self.cache.add_cache_entry(
                        media_path,
                        "thumbnails",
                        cache_path,
                        {
                            "interval": interval,
                            "positions": positions,
                            "width": 160,
                            "height": 90
                        }
                    )
                    return str(cache_path)
                return None
            except Exception as e:
                logger.error(f"Failed to generate thumbnails: {e}")
                try:
                    import shutil
                    shutil.rmtree(cache_path)
                except:
                    pass
                return None
            
        return self.job_manager.submit_job(
            job_type=JobType.CACHE_GENERATION,
            work_fn=work_fn
        )
    
    def generate_preview(self, media_path: str, preview_duration: int = 5) -> str:
        """
        Queue preview generation for a media file.
        
        Creates a short, low-quality preview of the video for quick playback.
        Preview will be 5 seconds from middle of video by default.
        """
        def work_fn():
            from utils.ffmpeg_wrapper import FFmpegWrapper
            ffmpeg = FFmpegWrapper()
            
            cache_path = self.cache.get_cache_path(media_path, "preview")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Get video duration to find middle point
                video_info = ffmpeg.get_video_info(media_path)
                total_duration = video_info['duration']
                
                # Start from middle - half preview duration
                start_time = max(0, (total_duration - preview_duration) / 2)
                
                # Generate preview using extract_clip with low quality settings
                from core.video_engine import ProcessingOptions
                options = ProcessingOptions(
                    width=426,  # 240p
                    maintain_aspect_ratio=True,
                    video_codec='h264',
                    video_preset='ultrafast',
                    video_crf=30,  # Very low quality for quick preview
                    audio_codec='aac',
                    audio_bitrate='32k',
                    fps=15,  # Lower framerate
                    use_gpu=True
                )
                
                ffmpeg.extract_clip(
                    media_path,
                    str(cache_path),
                    start_time,
                    start_time + preview_duration,
                    options
                )
                
                self.cache.add_cache_entry(
                    media_path,
                    "preview",
                    cache_path,
                    {
                        "start_time": start_time,
                        "duration": preview_duration,
                        "width": 426
                    }
                )
                return str(cache_path)
            except Exception as e:
                logger.error(f"Failed to generate preview: {e}")
                if cache_path.exists():
                    cache_path.unlink()
                return None
            
        return self.job_manager.submit_job(
            job_type=JobType.CACHE_GENERATION,
            work_fn=work_fn
        )
    
    def get_cached_path(self, media_path: str, cache_type: str) -> Optional[str]:
        """Get the path to cached media data if it exists."""
        if self.cache and self.cache.has_cache(media_path, cache_type):
            return str(self.cache.get_cache_path(media_path, cache_type))
        return None
    
    def clear_cache(self, media_path: Optional[str] = None,
                   cache_type: Optional[str] = None):
        """Clear cached data for a media file or cache type."""
        if self.cache:
            if media_path:
                self.cache.remove_cache(media_path, cache_type)
            elif cache_type:
                # Remove all cache of this type
                cache_dir = self.cache.cache_dir / cache_type
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cache_dir.mkdir()