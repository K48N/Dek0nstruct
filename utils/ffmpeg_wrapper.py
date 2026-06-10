"""
Low-level FFmpeg wrapper with GPU acceleration support
"""
import subprocess
import json
import os
import shutil
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from config import config


logger = logging.getLogger(__name__)


class FFmpegWrapper:
    """Professional FFmpeg wrapper with GPU support"""

    CPU_CODEC_MAP = {
        'h264': 'libx264',
        'h265': 'libx265',
    }
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        self.gpu_available = self._check_gpu_support()
        self.debug_mode = bool(config.get("app", "debug_mode"))
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            try:
                result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return ffmpeg_path
            except Exception:
                pass

        # Fallback to known local user install path
        local_ffmpeg = Path(os.getenv('LOCALAPPDATA', '')) / 'Programs' / 'ffmpeg' / 'current' / 'bin' / 'ffmpeg.exe'
        if local_ffmpeg.exists():
            return str(local_ffmpeg)

        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return 'ffmpeg'
        except Exception:
            pass
        return None
    
    def _find_ffprobe(self) -> str:
        """Find FFprobe executable"""
        ffprobe_path = shutil.which('ffprobe')
        if ffprobe_path:
            try:
                result = subprocess.run([ffprobe_path, '-version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return ffprobe_path
            except Exception:
                pass

        # If ffmpeg was found by absolute path, try sibling ffprobe binary.
        if self.ffmpeg_path and Path(self.ffmpeg_path).is_absolute():
            sibling_name = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'
            sibling = Path(self.ffmpeg_path).parent / sibling_name
            if sibling.exists():
                return str(sibling)

        # Fallback to known local user install path
        local_ffprobe = Path(os.getenv('LOCALAPPDATA', '')) / 'Programs' / 'ffmpeg' / 'current' / 'bin' / 'ffprobe.exe'
        if local_ffprobe.exists():
            return str(local_ffprobe)

        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return 'ffprobe'
        except Exception:
            pass
        return None
    
    def _check_gpu_support(self) -> Dict[str, bool]:
        """Check available GPU encoders"""
        gpu_support = {
            'nvenc': False,  # NVIDIA
            'qsv': False,    # Intel Quick Sync
            'videotoolbox': False,  # Apple
            'amf': False     # AMD
        }

        if not self.ffmpeg_path:
            return gpu_support
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout.lower()
            
            if 'h264_nvenc' in output:
                gpu_support['nvenc'] = True
            if 'h264_qsv' in output:
                gpu_support['qsv'] = True
            if 'h264_videotoolbox' in output:
                gpu_support['videotoolbox'] = True
            if 'h264_amf' in output:
                gpu_support['amf'] = True
        except Exception:
            pass
        
        return gpu_support
    
    def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive video information using ffprobe"""
        if not self.ffprobe_path:
            raise RuntimeError("FFprobe not available")
        
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=10, check=True)
            data = json.loads(result.stdout)
            fmt = data.get('format', {})
            
            # Extract useful information
            info = {
                'duration': self._safe_float(fmt.get('duration', 0.0)),
                'size': self._safe_int(fmt.get('size', 0)),
                'bitrate': self._safe_int(fmt.get('bit_rate', 0)),
                'format': fmt.get('format_name', 'unknown'),
                'streams': []
            }
            
            for stream in data.get('streams', []):
                stream_info = {
                    'type': stream.get('codec_type'),
                    'codec': stream.get('codec_name'),
                    'index': stream.get('index')
                }
                
                if stream.get('codec_type') == 'video':
                    stream_info.update({
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'fps': self._parse_fps(stream.get('r_frame_rate', '0/1')),
                        'pix_fmt': stream.get('pix_fmt')
                    })
                elif stream.get('codec_type') == 'audio':
                    stream_info.update({
                        'channels': stream.get('channels'),
                        'sample_rate': stream.get('sample_rate'),
                        'channel_layout': stream.get('channel_layout')
                    })
                
                info['streams'].append(stream_info)
            
            return info
            
        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {str(e)}")

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Convert ffprobe numeric fields safely."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Convert ffprobe numeric fields safely."""
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _parse_fps(self, value: Any) -> float:
        """Parse ffprobe frame-rate fields like '30000/1001' without eval."""
        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return 0.0

        rate = value.strip()
        if '/' in rate:
            num_str, den_str = rate.split('/', 1)
            num = self._safe_float(num_str)
            den = self._safe_float(den_str)
            if den == 0.0:
                return 0.0
            return num / den

        return self._safe_float(rate)
    
    def extract_clip(
        self,
        input_path: str,
        output_path: str,
        start: float,
        end: float,
        options = None  # ProcessingOptions
    ) -> None:
        """
        Extract video clip with processing options
        
        Args:
            input_path: Source video file
            output_path: Output file path
            start: Start time in seconds
            end: End time in seconds
            options: ProcessingOptions instance with encoding settings
        """
        if options is None:
            raise ValueError("Processing options are required")
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not available")

        duration = end - start
        output_ext = Path(output_path).suffix.lstrip('.').lower()
        is_audio_only = output_ext in {"mp3", "wav", "aac", "flac", "ogg"} or options.video_codec is None
        compatibility_mode = bool(getattr(options, "compatibility_mode", True))
        
        cmd = [
            self.ffmpeg_path,
            '-y',  # Overwrite
            '-ss', str(start),  # Seek to start
            '-i', input_path,
            '-t', str(duration),  # Duration
        ]

        if self.debug_mode:
            cmd.extend(['-loglevel', 'verbose'])
        else:
            cmd.extend(['-loglevel', 'error'])
        
        # Video encoding
        if is_audio_only:
            cmd.extend(['-vn'])
        elif options.codec_copy and not compatibility_mode:
            cmd.extend(['-c:v', 'copy'])
        else:
            # Select codec based on GPU support and settings
            video_codec_request = options.video_codec or 'h264'
            if compatibility_mode:
                video_codec_request = self._compatible_video_codec(output_ext)

            if options.use_gpu and video_codec_request == 'h264' and not compatibility_mode:
                if self.gpu_available['nvenc']:
                    codec = 'h264_nvenc'
                elif self.gpu_available['qsv']:
                    codec = 'h264_qsv'
                elif self.gpu_available['videotoolbox']:
                    codec = 'h264_videotoolbox'
                else:
                    codec = self.CPU_CODEC_MAP.get(video_codec_request, video_codec_request)
            else:
                codec = self.CPU_CODEC_MAP.get(video_codec_request, video_codec_request)
            
            cmd.extend(['-c:v', codec])
            
            # Video quality settings
            if options.video_preset:
                cmd.extend(['-preset', options.video_preset])
            
            if options.video_crf is not None:
                cmd.extend(['-crf', str(options.video_crf)])
            
            if options.video_bitrate:
                cmd.extend(['-b:v', options.video_bitrate])
            
            if compatibility_mode:
                cmd.extend(['-pix_fmt', 'yuv420p'])
            elif options.video_pixel_format:
                cmd.extend(['-pix_fmt', options.video_pixel_format])
        
            # Resolution settings
            if options.width and options.height:
                if options.maintain_aspect_ratio:
                    cmd.extend([
                        '-vf',
                        f'scale={options.width}:{options.height}:force_original_aspect_ratio=decrease'
                    ])
                else:
                    cmd.extend(['-vf', f'scale={options.width}:{options.height}'])
            
            # FPS settings
            if options.fps:
                cmd.extend(['-r', str(options.fps)])

            cmd.extend(self._container_compat_args(output_ext))
        
        # Audio encoding
        if options.codec_copy and not compatibility_mode and not is_audio_only:
            cmd.extend(['-c:a', 'copy'])
        else:
            audio_codec = options.audio_codec or self._compatible_audio_codec(output_ext)
            if compatibility_mode:
                audio_codec = self._compatible_audio_codec(output_ext)
            cmd.extend(['-c:a', audio_codec])
            
            if options.audio_channels == 'mono':
                cmd.extend(['-ac', '1'])
            elif options.audio_channels == 'stereo':
                cmd.extend(['-ac', '2'])
            
            if options.audio_sample_rate:
                cmd.extend(['-ar', str(options.audio_sample_rate)])
            
            if options.audio_bitrate:
                cmd.extend(['-b:a', options.audio_bitrate])
            
            if options.normalize_audio:
                cmd.extend(['-filter:a', 'loudnorm'])
        
        # Metadata
        if options.metadata:
            for key, value in options.metadata.items():
                cmd.extend(['-metadata', f"{key}={value}"])
        
        # Additional options
        cmd.extend([
            '-avoid_negative_ts', '1',
            '-max_muxing_queue_size', '1024'
        ])
        
        # Extra arguments
        if options.extra_args:
            cmd.extend(options.extra_args)
        
        cmd.append(output_path)

        if self.debug_mode:
            logger.debug("FFmpeg command: %s", " ".join(str(part) for part in cmd))
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Extraction timed out (600s limit)")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr or b"").decode(errors="replace")
            raise RuntimeError(f"FFmpeg failed: {stderr}")

    def _compatible_video_codec(self, output_ext: str) -> str:
        """Return a broadly supported video codec for the selected container."""
        codec_map = {
            'webm': 'libvpx-vp9',
            'avi': 'mpeg4',
            'mkv': 'h264',
            'mov': 'h264',
            'mp4': 'h264',
        }
        return codec_map.get(output_ext, 'h264')

    def _compatible_audio_codec(self, output_ext: str) -> str:
        """Return a broadly supported audio codec for the selected container."""
        codec_map = {
            'mp3': 'libmp3lame',
            'wav': 'pcm_s16le',
            'aac': 'aac',
            'flac': 'flac',
            'ogg': 'libvorbis',
            'webm': 'libopus',
            'avi': 'libmp3lame',
            'mkv': 'aac',
            'mov': 'aac',
            'mp4': 'aac',
        }
        return codec_map.get(output_ext, 'aac')

    def _container_compat_args(self, output_ext: str) -> List[str]:
        """Container-level flags that improve compatibility across players/devices."""
        if output_ext == 'mp4':
            return ['-movflags', '+faststart', '-profile:v', 'high', '-level', '4.1']
        if output_ext == 'mov':
            return ['-movflags', '+faststart', '-tag:v', 'avc1']
        return []
    
    def is_preview_compatible(self, path: str) -> bool:
        """Return True if the file is already H264+AAC in an MP4/MOV container."""
        try:
            info = self.get_video_info(path)
        except Exception:
            return False
        fmt = info.get('format', '')
        if not any(f in fmt for f in ('mp4', 'mov', 'isom', 'quicktime')):
            return False
        v_ok = any(
            s['type'] == 'video' and s.get('codec') in ('h264', 'avc')
            for s in info.get('streams', [])
        )
        a_streams = [s for s in info.get('streams', []) if s['type'] == 'audio']
        a_ok = (not a_streams) or any(
            s.get('codec') in ('aac', 'mp3', 'mp4a') for s in a_streams
        )
        return v_ok and a_ok

    def transcode_for_preview(self, src: str, dst: str,
                              duration: float = 0.0,
                              progress_cb=None) -> bool:
        """Transcode any video to H264/AAC MP4 so QMediaPlayer can play it.
        progress_cb(fraction: float, eta_seconds: float) is called on each update.
        """
        import time
        if not self.ffmpeg_path:
            return False
        cmd = [
            self.ffmpeg_path, '-y',
            '-progress', 'pipe:1', '-nostats',
            '-i', src,
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            dst,
        ]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
            start = time.time()
            out_us = 0
            total_us = duration * 1_000_000 if duration > 0 else 0
            for line in proc.stdout:
                line = line.strip()
                if line.startswith('out_time_us='):
                    try:
                        out_us = int(line.split('=', 1)[1])
                    except ValueError:
                        pass
                    if progress_cb and total_us > 0 and out_us > 0:
                        fraction = min(out_us / total_us, 1.0)
                        elapsed = time.time() - start
                        eta = (elapsed / fraction) * (1.0 - fraction) if fraction > 0 else 0
                        progress_cb(fraction, eta)
            proc.wait(timeout=300)
            return proc.returncode == 0
        except Exception:
            return False

    def generate_thumbnail(
        self,
        video_path: str,
        output_path: str,
        time_position: float,
        width: int = 320,
        height: int = 180
    ) -> bool:
        """Generate thumbnail at specific timestamp"""
        if not self.ffmpeg_path:
            return False

        cmd = [
            self.ffmpeg_path,
            '-y',
            '-ss', str(time_position),
            '-i', video_path,
            '-vframes', '1',
            '-s', f'{width}x{height}',
            '-f', 'image2',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            return True
        except Exception:
            return False
    
    def generate_waveform(
        self,
        video_path: str,
        output_path: str,
        width: int = 1200,
        height: int = 100
    ) -> bool:
        """Generate waveform visualization"""
        if not self.ffmpeg_path:
            return False

        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-filter_complex',
            f'showwavespic=s={width}x{height}:colors=009682',
            '-frames:v', '1',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            return True
        except Exception:
            return False