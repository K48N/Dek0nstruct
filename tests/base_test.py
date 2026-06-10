"""Base test configuration and utilities."""
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from config import Config
from services.service_registry import ServiceRegistry
from services.background_job_manager import BackgroundJobManager
from services.media_cache_service import MediaCacheService
from services.ai_service import AIService
from services.audio_enhancement_service import AudioEnhancementService
from services.export_queue_service import ExportQueueService

class BaseServiceTest(unittest.TestCase):
    """Base class for service tests."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        
        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.test_dir))
        
        # Initialize services
        self.registry = ServiceRegistry()
        
        # Register common services
        self.registry.register(BackgroundJobManager)
        self.registry.register(MediaCacheService)
        self.registry.register(AIService)
        self.registry.register(AudioEnhancementService)
        self.registry.register(ExportQueueService)
        
        self.addCleanup(self.registry.cleanup)
        
        # Override config for testing
        self.config = self._create_test_config()
        
        yield
    
    def _create_test_config(self) -> Dict[str, Any]:
        """Create test configuration."""
        return {
            "ai": {
                "whisper_model": "tiny",
                "enable_scene_detection": True,
                "enable_speaker_diarization": False,
                "auto_summarize_length": 30,
                "confidence_threshold": 0.5
            },
            "audio": {
                "voice_clarity": {
                    "default_strength": 0.5,
                    "enable_noise_reduction": True
                },
                "music_ducking": {
                    "threshold": -20,
                    "reduction": -10
                },
                "style_matching": {
                    "target_loudness": -18,
                    "enable_eq_matching": True
                }
            },
            "cache": {
                "max_size_gb": 1,
                "max_age_days": 1,
                "generate_on_import": True,
                "proxy_resolution": "480p",
                "thumbnail_interval": 1.0
            },
            "export": {
                "max_concurrent_jobs": 1,
                "default_format": "mp4",
                "temp_directory": str(self.test_dir / "temp")
            }
        }
    
    def create_temp_file(self, name: str, content: bytes = b"") -> Path:
        """Create a temporary file for testing."""
        path = self.test_dir / name
        path.write_bytes(content)
        return path
    
    def addCleanup(self, func):
        """Add cleanup function to be run after test."""
        if not hasattr(self, '_cleanup_functions'):
            self._cleanup_functions = []
        self._cleanup_functions.append(func)
    
    def doCleanups(self):
        """Run all cleanup functions."""
        if hasattr(self, '_cleanup_functions'):
            while self._cleanup_functions:
                func = self._cleanup_functions.pop()
                try:
                    func()
                except Exception as e:
                    print(f"Cleanup failed: {e}")