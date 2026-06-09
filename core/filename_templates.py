"""
Filename template system for export customization
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import re


class FilenameTemplate:
    """Handle filename templates with variables"""
    
    VARIABLES = {
        '{label}': 'Segment label',
        '{start}': 'Start time in seconds',
        '{end}': 'End time in seconds',
        '{duration}': 'Duration in seconds',
        '{start_time}': 'Start time as HH-MM-SS',
        '{end_time}': 'End time as HH-MM-SS',
        '{index}': 'Segment index (1, 2, 3...)',
        '{date}': 'Current date (YYYY-MM-DD)',
        '{time}': 'Current time (HH-MM-SS)',
        '{video}': 'Source video filename',
        '{project}': 'Project name'
    }
    
    DEFAULT_TEMPLATE = "{label}_{start}_{end}"
    
    def __init__(self, template: str = None):
        self.template = template or self.DEFAULT_TEMPLATE
    
    def format(self, **kwargs) -> str:
        """
        Format template with provided variables
        
        Args:
            label: Segment label
            start: Start time in seconds
            end: End time in seconds
            duration: Duration in seconds
            index: Segment index
            video_path: Source video path
            project_name: Project name
        
        Returns:
            Formatted filename
        """
        result = self.template
        
        # Simple replacements
        replacements = {
            '{label}': kwargs.get('label', 'Untitled'),
            '{start}': str(int(kwargs.get('start', 0))),
            '{end}': str(int(kwargs.get('end', 0))),
            '{duration}': str(int(kwargs.get('duration', 0))),
            '{index}': str(kwargs.get('index', 1)),
            '{date}': datetime.now().strftime('%Y-%m-%d'),
            '{time}': datetime.now().strftime('%H-%M-%S'),
            '{project}': kwargs.get('project_name', 'project')
        }
        
        # Time formatting
        if '{start_time}' in result:
            replacements['{start_time}'] = self._format_time(kwargs.get('start', 0))
        
        if '{end_time}' in result:
            replacements['{end_time}'] = self._format_time(kwargs.get('end', 0))
        
        # Video filename
        if '{video}' in result:
            video_path = kwargs.get('video_path', '')
            if video_path:
                replacements['{video}'] = Path(video_path).stem
            else:
                replacements['{video}'] = 'video'
        
        # Apply replacements
        for var, value in replacements.items():
            result = result.replace(var, self._sanitize(value))
        
        return result
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as HH-MM-SS"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}-{m:02d}-{s:02d}"
    
    def _sanitize(self, text: str) -> str:
        """Remove invalid filename characters"""
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '_', text)
        # Remove leading/trailing spaces and dots
        text = text.strip('. ')
        return text
    
    def validate(self) -> tuple:
        """
        Validate template
        
        Returns:
            (is_valid, error_message)
        """
        # Check for unknown variables
        pattern = r'\{([^}]+)\}'
        variables = re.findall(pattern, self.template)
        
        unknown = [v for v in variables if f'{{{v}}}' not in self.VARIABLES]
        if unknown:
            return False, f"Unknown variables: {', '.join(unknown)}"
        
        # Check if template will produce valid filenames
        test_result = self.format(
            label="Test",
            start=0,
            end=100,
            duration=100,
            index=1
        )
        
        if not test_result or test_result.strip() == '':
            return False, "Template produces empty filename"
        
        return True, ""
    
    def preview(self, **kwargs) -> str:
        """Generate preview of formatted filename"""
        return self.format(**kwargs)
    
    @classmethod
    def get_presets(cls) -> Dict[str, str]:
        """Get predefined templates"""
        return {
            'Simple': '{label}_{index}',
            'Detailed': '{label}_{start}_{end}',
            'Timestamp': '{label}_{start_time}',
            'Dated': '{date}_{label}_{index}',
            'Project Based': '{project}_{label}_{index}',
            'Full': '{project}_{label}_{start_time}-{end_time}_{date}'
        }