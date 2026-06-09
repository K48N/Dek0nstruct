"""
Professional undo/redo system with command pattern
"""
from typing import List, Optional, Any, Callable
from abc import ABC, abstractmethod


class Command(ABC):
    """Abstract command for undo/redo operations"""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command"""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Get command description for UI"""
        pass


class AddSegmentCommand(Command):
    """Command to add a segment"""
    
    def __init__(self, segment_list: List, segment: Any):
        self.segment_list = segment_list
        self.segment = segment
    
    def execute(self) -> None:
        self.segment_list.append(self.segment)
    
    def undo(self) -> None:
        self.segment_list.remove(self.segment)
    
    def description(self) -> str:
        return f"Add '{self.segment.label}'"


class RemoveSegmentCommand(Command):
    """Command to remove a segment"""
    
    def __init__(self, segment_list: List, segment: Any):
        self.segment_list = segment_list
        self.segment = segment
        self.index = -1
    
    def execute(self) -> None:
        self.index = self.segment_list.index(self.segment)
        self.segment_list.remove(self.segment)
    
    def undo(self) -> None:
        self.segment_list.insert(self.index, self.segment)
    
    def description(self) -> str:
        return f"Remove '{self.segment.label}'"


class ModifySegmentCommand(Command):
    """Command to modify a segment"""
    
    def __init__(self, segment: Any, attr: str, old_value: Any, new_value: Any):
        self.segment = segment
        self.attr = attr
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self) -> None:
        setattr(self.segment, self.attr, self.new_value)
    
    def undo(self) -> None:
        setattr(self.segment, self.attr, self.old_value)
    
    def description(self) -> str:
        return f"Modify '{self.segment.label}' {self.attr}"


class BatchCommand(Command):
    """Execute multiple commands as one"""
    
    def __init__(self, commands: List[Command], desc: str = "Batch operation"):
        self.commands = commands
        self.desc = desc
    
    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()
    
    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()
    
    def description(self) -> str:
        return self.desc


class UndoManager:
    """Manages undo/redo history"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._callbacks: List[Callable] = []
    
    def execute(self, command: Command) -> None:
        """Execute a command and add to history"""
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()
        
        # Limit history size
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        
        self._notify_change()
    
    def undo(self) -> bool:
        """Undo last command"""
        if not self.can_undo():
            return False
        
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self._notify_change()
        return True
    
    def redo(self) -> bool:
        """Redo last undone command"""
        if not self.can_redo():
            return False
        
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self._notify_change()
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self._redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo operation"""
        if not self.can_undo():
            return None
        return self._undo_stack[-1].description()
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo operation"""
        if not self.can_redo():
            return None
        return self._redo_stack[-1].description()
    
    def clear(self) -> None:
        """Clear all history"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_change()
    
    def add_callback(self, callback: Callable) -> None:
        """Add callback for state changes"""
        self._callbacks.append(callback)
    
    def _notify_change(self) -> None:
        """Notify callbacks of state change"""
        for callback in self._callbacks:
            callback()
    
    def get_history(self) -> List[str]:
        """Get list of undo history descriptions"""
        return [cmd.description() for cmd in self._undo_stack]