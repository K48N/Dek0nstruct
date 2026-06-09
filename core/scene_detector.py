"""FFmpeg-based scene and silence detection."""
import subprocess
import re
import logging
from typing import List

from core.segment import Segment

logger = logging.getLogger(__name__)


class SceneDetector:
    """Detect scene changes and silence using FFmpeg only."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def detect_scenes(
        self,
        video_path: str,
        threshold: float = 0.3,
        min_scene_length: float = 2.0,
        duration: float = 0.0,
    ) -> List[Segment]:
        """Detect scene changes via ffmpeg scene filter."""
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-filter:v", f"select=gt(scene\\,{threshold}),showinfo",
            "-f", "null", "-",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except Exception as e:
            raise RuntimeError(f"Scene detection failed: {e}")
        timestamps = self._parse_pts_timestamps(result.stderr)
        return self._cuts_to_segments(timestamps, duration, min_scene_length)

    def detect_silence(
        self,
        video_path: str,
        noise_threshold: str = "-30dB",
        min_silence_duration: float = 1.0,
        duration: float = 0.0,
    ) -> List[Segment]:
        """Detect non-silent regions as segments."""
        cmd = [
            self.ffmpeg_path, "-i", video_path,
            "-af", f"silencedetect=n={noise_threshold}:d={min_silence_duration}",
            "-f", "null", "-",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except Exception as e:
            raise RuntimeError(f"Silence detection failed: {e}")
        silences = self._parse_silence(result.stderr)
        return self._silence_to_segments(silences, duration)

    # ---- private --------------------------------------------------------

    def _parse_pts_timestamps(self, stderr: str) -> List[float]:
        times: List[float] = []
        for line in stderr.splitlines():
            m = re.search(r"pts_time:([\d.]+)", line)
            if m:
                times.append(float(m.group(1)))
        return sorted(set(times))

    def _cuts_to_segments(
        self, cuts: List[float], duration: float, min_len: float
    ) -> List[Segment]:
        boundaries = [0.0] + cuts + ([duration] if duration > 0 else [])
        segments: List[Segment] = []
        for i in range(len(boundaries) - 1):
            start, end = boundaries[i], boundaries[i + 1]
            if end - start >= min_len:
                segments.append(Segment(start=start, end=end, label=f"Scene {i + 1}"))
        return segments

    def _parse_silence(self, stderr: str) -> List[tuple]:
        starts, ends = [], []
        for line in stderr.splitlines():
            ms = re.search(r"silence_start: ([\d.]+)", line)
            me = re.search(r"silence_end: ([\d.]+)", line)
            if ms:
                starts.append(float(ms.group(1)))
            if me:
                ends.append(float(me.group(1)))
        return list(zip(starts, ends))

    def _silence_to_segments(
        self, silences: List[tuple], duration: float
    ) -> List[Segment]:
        if not silences:
            return []
        segments: List[Segment] = []
        prev_end = 0.0
        for i, (s_start, s_end) in enumerate(silences):
            if s_start - prev_end > 0.5:
                segments.append(
                    Segment(start=prev_end, end=s_start, label=f"Part {i + 1}")
                )
            prev_end = s_end
        if duration > 0 and duration - prev_end > 0.5:
            segments.append(
                Segment(start=prev_end, end=duration, label=f"Part {len(segments) + 1}")
            )
        return segments
