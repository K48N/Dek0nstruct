"""
Segment model with validation and serialization
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Segment:
    """Represents a video segment with validation"""
    
    start: float
    end: float
    label: str = "Untitled"
    color: str = "#009682"
    export_video: bool = True
    export_audio: bool = True
    
    def __post_init__(self):
        """Validate segment after initialization"""
        self.validate()
    
    @property
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end - self.start
    
    def validate(self) -> None:
        """Validate segment parameters"""
        if self.start < 0:
            raise ValueError(f"Start time cannot be negative: {self.start}")
        if self.end <= self.start:
            raise ValueError(f"End time ({self.end}) must be greater than start time ({self.start})")
        if not self.label or not self.label.strip():
            self.label = f"Part {id(self)}"
    
    def overlaps_with(self, other: 'Segment') -> bool:
        """Check if this segment overlaps with another"""
        return not (self.end <= other.start or self.start >= other.end)
    
    def contains_time(self, time: float) -> bool:
        """Check if time falls within this segment"""
        return self.start <= time <= self.end
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'start': self.start,
            'end': self.end,
            'label': self.label,
            'color': self.color,
            'export_video': self.export_video,
            'export_audio': self.export_audio
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Segment':
        """Create segment from dictionary"""
        return cls(
            start=data['start'],
            end=data['end'],
            label=data.get('label', 'Untitled'),
            color=data.get('color', '#009682'),
            export_video=data.get('export_video', True),
            export_audio=data.get('export_audio', True)
        )
    
    def __repr__(self) -> str:
        return f"Segment('{self.label}', {self.start:.2f}s-{self.end:.2f}s)"