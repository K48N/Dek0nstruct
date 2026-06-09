from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading
import logging
import uuid

from models.export_job import ExportJob, JobStatus, JobType

logger = logging.getLogger(__name__)

class Service(ABC):
    """Base class for all services in the application."""
    
    def __init__(self):
        self._is_running = False
        self._executor = None
        
    @abstractmethod
    def start(self) -> None:
        """Initialize and start the service."""
        self._is_running = True
        self._executor = ThreadPoolExecutor()
    
    @abstractmethod
    def stop(self) -> None:
        """Stop and cleanup the service."""
        self._is_running = False
        if self._executor:
            self._executor.shutdown(wait=True)
            
    @property
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._is_running