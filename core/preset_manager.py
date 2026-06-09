"""
Export preset management for saving/loading common configurations
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from core.video_engine import ProcessingOptions


class PresetManager:
    """Manage export presets"""
    
    def __init__(self, presets_dir: Optional[str] = None):
        if presets_dir:
            self.presets_dir = Path(presets_dir)
        else:
            # Use user's home directory
            self.presets_dir = Path.home() / '.video_editor' / 'presets'
        
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        # Built-in presets
        self.builtin_presets = {
            'Fast & Small (Mono)': ProcessingOptions(
                audio_channels='mono',
                use_gpu=True,
                codec_copy=True,
                mp3_quality=5,
                output_format='mp4',
                parallel_processing=True,
                max_workers=4
            ),
            'Best Quality (Stereo)': ProcessingOptions(
                audio_channels='stereo',
                use_gpu=True,
                codec_copy=False,
                mp3_quality=0,
                output_format='mp4',
                parallel_processing=True,
                max_workers=4
            ),
            'Conference Recording': ProcessingOptions(
                audio_channels='mono',
                use_gpu=True,
                codec_copy=True,
                mp3_quality=2,
                output_format='mp4',
                parallel_processing=True,
                max_workers=6
            ),
            'Music Video': ProcessingOptions(
                audio_channels='stereo',
                use_gpu=True,
                codec_copy=False,
                mp3_quality=0,
                output_format='mp4',
                parallel_processing=True,
                max_workers=2
            ),
            'Archive (MKV)': ProcessingOptions(
                audio_channels=None,
                use_gpu=False,
                codec_copy=True,
                mp3_quality=2,
                output_format='mkv',
                parallel_processing=True,
                max_workers=8
            )
        }
    
    def save_preset(self, name: str, options: ProcessingOptions) -> bool:
        """Save an export preset"""
        try:
            preset_path = self.presets_dir / f"{name}.json"
            
            data = {
                'audio_channels': options.audio_channels,
                'use_gpu': options.use_gpu,
                'codec_copy': options.codec_copy,
                'mp3_quality': options.mp3_quality,
                'output_format': options.output_format,
                'parallel_processing': options.parallel_processing,
                'max_workers': options.max_workers
            }
            
            with open(preset_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except:
            return False
    
    def load_preset(self, name: str) -> Optional[ProcessingOptions]:
        """Load an export preset"""
        # Check built-in presets first
        if name in self.builtin_presets:
            return self.builtin_presets[name]
        
        # Check user presets
        try:
            preset_path = self.presets_dir / f"{name}.json"
            
            if not preset_path.exists():
                return None
            
            with open(preset_path, 'r') as f:
                data = json.load(f)
            
            return ProcessingOptions(
                audio_channels=data.get('audio_channels'),
                use_gpu=data.get('use_gpu', True),
                codec_copy=data.get('codec_copy', True),
                mp3_quality=data.get('mp3_quality', 2),
                output_format=data.get('output_format', 'mp4'),
                parallel_processing=data.get('parallel_processing', True),
                max_workers=data.get('max_workers', 4)
            )
        except:
            return None
    
    def delete_preset(self, name: str) -> bool:
        """Delete a user preset"""
        # Don't allow deleting built-in presets
        if name in self.builtin_presets:
            return False
        
        try:
            preset_path = self.presets_dir / f"{name}.json"
            if preset_path.exists():
                preset_path.unlink()
                return True
        except:
            pass
        
        return False
    
    def list_presets(self) -> List[str]:
        """List all available presets"""
        # Built-in presets
        presets = list(self.builtin_presets.keys())
        
        # User presets
        if self.presets_dir.exists():
            for path in self.presets_dir.glob('*.json'):
                preset_name = path.stem
                if preset_name not in presets:
                    presets.append(preset_name)
        
        return sorted(presets)
    
    def is_builtin(self, name: str) -> bool:
        """Check if preset is built-in"""
        return name in self.builtin_presets
    
    def export_presets(self, export_path: str) -> bool:
        """Export all user presets to a file"""
        try:
            user_presets = {}
            
            for preset_name in self.list_presets():
                if not self.is_builtin(preset_name):
                    options = self.load_preset(preset_name)
                    if options:
                        user_presets[preset_name] = {
                            'audio_channels': options.audio_channels,
                            'use_gpu': options.use_gpu,
                            'codec_copy': options.codec_copy,
                            'mp3_quality': options.mp3_quality,
                            'output_format': options.output_format,
                            'parallel_processing': options.parallel_processing,
                            'max_workers': options.max_workers
                        }
            
            with open(export_path, 'w') as f:
                json.dump(user_presets, f, indent=2)
            
            return True
        except:
            return False
    
    def import_presets(self, import_path: str) -> int:
        """Import presets from a file, returns number imported"""
        try:
            with open(import_path, 'r') as f:
                presets = json.load(f)
            
            count = 0
            for name, data in presets.items():
                options = ProcessingOptions(
                    audio_channels=data.get('audio_channels'),
                    use_gpu=data.get('use_gpu', True),
                    codec_copy=data.get('codec_copy', True),
                    mp3_quality=data.get('mp3_quality', 2),
                    output_format=data.get('output_format', 'mp4'),
                    parallel_processing=data.get('parallel_processing', True),
                    max_workers=data.get('max_workers', 4)
                )
                
                if self.save_preset(name, options):
                    count += 1
            
            return count
        except:
            return 0