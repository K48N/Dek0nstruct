"""
Advanced audio processing with Demucs for music removal
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple


class AudioProcessor:
    """Audio processing with Demucs and FFmpeg"""
    
    def __init__(self):
        self.demucs_available = self._check_demucs()
        self.ffmpeg_path = 'ffmpeg'
    
    def _check_demucs(self) -> bool:
        """Check if Demucs is installed"""
        try:
            import demucs.separate
            return True
        except ImportError:
            return False
    
    def remove_music(
        self,
        input_path: str,
        output_path: str,
        keep_vocals: bool = True,
        model: str = "htdemucs"
    ) -> bool:
        """
        Remove background music using Demucs
        
        Args:
            input_path: Input video/audio file
            output_path: Output file path
            keep_vocals: True = keep vocals, False = keep music
            model: Demucs model (htdemucs, htdemucs_ft, htdemucs_6s)
        
        Returns:
            True if successful
        """
        if not self.demucs_available:
            raise RuntimeError(
                "Demucs not installed. Install with: pip install demucs"
            )
        
        try:
            import torch
            from demucs.pretrained import get_model
            from demucs.apply import apply_model
            from demucs.audio import AudioFile, save_audio
            
            # Load model
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            demucs_model = get_model(model)
            demucs_model.to(device)
            
            # Load audio
            wav = AudioFile(input_path).read(
                streams=0,
                samplerate=demucs_model.samplerate,
                channels=demucs_model.audio_channels
            )
            
            # Separate sources
            ref = wav.mean(0)
            wav = (wav - ref.mean()) / ref.std()
            
            sources = apply_model(
                demucs_model,
                wav[None],
                device=device,
                progress=True
            )[0]
            
            sources = sources * ref.std() + ref.mean()
            
            # Extract vocals or music
            if keep_vocals:
                output_audio = sources[3]  # vocals
            else:
                # Combine everything except vocals
                output_audio = sources[0] + sources[1] + sources[2]
            
            # Save
            save_audio(
                output_audio,
                output_path,
                samplerate=demucs_model.samplerate
            )
            
            return True
            
        except Exception as e:
            print(f"Demucs error: {str(e)}")
            return False
    
    def normalize_audio(
        self,
        input_path: str,
        output_path: str,
        target_level: float = -16.0
    ) -> bool:
        """
        Normalize audio to target loudness (LUFS)
        
        Args:
            input_path: Input file
            output_path: Output file
            target_level: Target loudness in LUFS (-23 to -5)
        """
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-af', f'loudnorm=I={target_level}:TP=-1.5:LRA=11',
                '-ar', '48000',
                output_path,
                '-y'
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=300
            )
            
            return True
            
        except Exception as e:
            print(f"Normalization error: {str(e)}")
            return False
    
    def reduce_noise(
        self,
        input_path: str,
        output_path: str,
        noise_reduction: int = 10
    ) -> bool:
        """
        Reduce background noise
        
        Args:
            input_path: Input file
            output_path: Output file
            noise_reduction: Reduction amount (0-100)
        """
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-af', f'afftdn=nf={noise_reduction}',
                output_path,
                '-y'
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=300
            )
            
            return True
            
        except Exception as e:
            print(f"Noise reduction error: {str(e)}")
            return False
    
    def apply_eq(
        self,
        input_path: str,
        output_path: str,
        bass: int = 0,
        mid: int = 0,
        treble: int = 0
    ) -> bool:
        """
        Apply equalizer adjustments
        
        Args:
            input_path: Input file
            output_path: Output file
            bass: Bass adjustment (-20 to +20 dB)
            mid: Mid adjustment (-20 to +20 dB)
            treble: Treble adjustment (-20 to +20 dB)
        """
        try:
            eq_filter = f'equalizer=f=100:t=h:w=200:g={bass},'
            eq_filter += f'equalizer=f=1000:t=h:w=200:g={mid},'
            eq_filter += f'equalizer=f=10000:t=h:w=200:g={treble}'
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-af', eq_filter,
                output_path,
                '-y'
            ]
            
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=300
            )
            
            return True
            
        except Exception as e:
            print(f"EQ error: {str(e)}")
            return False
    
    def process_video_audio(
        self,
        video_path: str,
        output_path: str,
        operation: str,
        **kwargs
    ) -> bool:
        """
        Process audio in video file
        
        Args:
            video_path: Input video
            output_path: Output video
            operation: 'remove_music', 'normalize', 'reduce_noise', 'eq'
            **kwargs: Operation-specific parameters
        """
        try:
            # Extract audio
            temp_audio = tempfile.mktemp(suffix='.wav')
            
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                temp_audio,
                '-y'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Process audio
            processed_audio = tempfile.mktemp(suffix='.wav')
            
            if operation == 'remove_music':
                success = self.remove_music(temp_audio, processed_audio, **kwargs)
            elif operation == 'normalize':
                success = self.normalize_audio(temp_audio, processed_audio, **kwargs)
            elif operation == 'reduce_noise':
                success = self.reduce_noise(temp_audio, processed_audio, **kwargs)
            elif operation == 'eq':
                success = self.apply_eq(temp_audio, processed_audio, **kwargs)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            if not success:
                return False
            
            # Merge with video
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-i', processed_audio,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v:0',
                '-map', '1:a:0',
                output_path,
                '-y'
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Cleanup
            os.remove(temp_audio)
            os.remove(processed_audio)
            
            return True
            
        except Exception as e:
            print(f"Video audio processing error: {str(e)}")
            return False
    
    def get_audio_info(self, file_path: str) -> dict:
        """Get audio stream information"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a:0',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            import json
            data = json.loads(result.stdout)
            
            if data.get('streams'):
                stream = data['streams'][0]
                return {
                    'codec': stream.get('codec_name'),
                    'sample_rate': stream.get('sample_rate'),
                    'channels': stream.get('channels'),
                    'channel_layout': stream.get('channel_layout'),
                    'bitrate': stream.get('bit_rate')
                }
            
            return {}
            
        except Exception:
            return {}