"""
Auto-save and crash recovery system
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from PyQt5.QtCore import QTimer


class AutoSaveManager:
    """Automatic project saving with crash recovery"""
    
    def __init__(self, interval_minutes: int = 5):
        self.interval_ms = interval_minutes * 60 * 1000
        self.enabled = True
        self.timer = QTimer()
        self.timer.timeout.connect(self._auto_save_callback)
        
        # Setup directories
        self.backup_dir = Path.home() / '.dek0nstruct' / 'autosave'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_project = None
        self.save_callback = None
    
    def set_save_callback(self, callback):
        """Set function to call for saving"""
        self.save_callback = callback
    
    def set_project(self, project_path: Optional[str]):
        """Set current project path"""
        self.current_project = project_path
    
    def start(self):
        """Start auto-save timer"""
        if self.enabled:
            self.timer.start(self.interval_ms)
    
    def stop(self):
        """Stop auto-save timer"""
        self.timer.stop()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable auto-save"""
        self.enabled = enabled
        if enabled:
            self.start()
        else:
            self.stop()
    
    def _auto_save_callback(self):
        """Called by timer to perform auto-save"""
        if not self.enabled or not self.save_callback:
            return
        
        try:
            # Create backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"autosave_{timestamp}.vedproj"
            
            # Call save callback
            self.save_callback(str(backup_path))
            
            # Clean old backups (keep last 10)
            self._cleanup_old_backups()
            
        except Exception as e:
            print(f"Auto-save failed: {str(e)}")
    
    def _cleanup_old_backups(self):
        """Remove old backup files"""
        backups = sorted(
            self.backup_dir.glob('autosave_*.vedproj'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Keep only last 10
        for backup in backups[10:]:
            try:
                backup.unlink()
            except:
                pass
    
    def get_recovery_files(self) -> List[dict]:
        """Get list of recoverable backup files"""
        backups = []
        
        for backup_path in self.backup_dir.glob('autosave_*.vedproj'):
            try:
                stat = backup_path.stat()
                backups.append({
                    'path': str(backup_path),
                    'name': backup_path.stem,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'size': stat.st_size
                })
            except:
                continue
        
        return sorted(backups, key=lambda b: b['modified'], reverse=True)
    
    def has_recovery_files(self) -> bool:
        """Check if recovery files exist"""
        return len(list(self.backup_dir.glob('autosave_*.vedproj'))) > 0
    
    def clear_recovery_files(self):
        """Clear all recovery files"""
        for backup in self.backup_dir.glob('autosave_*.vedproj'):
            try:
                backup.unlink()
            except:
                pass
    
    def recover_from_backup(self, backup_path: str, target_path: str):
        """Recover project from backup"""
        shutil.copy2(backup_path, target_path)