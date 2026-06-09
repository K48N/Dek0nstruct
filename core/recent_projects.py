"""
Recent projects management
"""
import json
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class RecentProjectsManager:
    """Manage recently opened projects"""
    
    def __init__(self, max_recent: int = 10):
        self.max_recent = max_recent
        self.config_dir = Path.home() / '.video_editor'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'recent_projects.json'
        self.projects = self._load()
    
    def _load(self) -> List[Dict]:
        """Load recent projects from config"""
        if not self.config_file.exists():
            return []
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            return data.get('projects', [])
        except:
            return []
    
    def _save(self):
        """Save recent projects to config"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'projects': self.projects}, f, indent=2)
        except:
            pass
    
    def add_project(self, project_path: str, video_path: str = None):
        """Add project to recent list"""
        if not os.path.exists(project_path):
            return
        
        # Remove if already exists
        self.projects = [p for p in self.projects if p['path'] != project_path]
        
        # Add to front
        self.projects.insert(0, {
            'path': project_path,
            'video': video_path,
            'name': Path(project_path).stem,
            'opened': datetime.now().isoformat()
        })
        
        # Limit size
        self.projects = self.projects[:self.max_recent]
        
        # Clean up missing files
        self._cleanup()
        
        self._save()
    
    def get_recent(self) -> List[Dict]:
        """Get list of recent projects"""
        self._cleanup()
        return self.projects
    
    def clear(self):
        """Clear all recent projects"""
        self.projects = []
        self._save()
    
    def _cleanup(self):
        """Remove projects with missing files"""
        self.projects = [
            p for p in self.projects 
            if os.path.exists(p['path'])
        ]
        self._save()