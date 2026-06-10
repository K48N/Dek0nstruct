from typing import Dict, Type
import logging
from .base_service import Service

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Manages all services in the application."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
        return cls._instance
    
    def register(self, service_class: Type[Service]) -> None:
        """Register a new service."""
        service_name = service_class.__name__
        if service_name not in self._services:
            logger.info(f"Registering service: {service_name}")
            self._services[service_name] = service_class()
    
    def get_service(self, service_class: Type[Service]) -> Service:
        """Get an instance of a registered service."""
        service_name = service_class.__name__
        if service_name not in self._services:
            raise KeyError(f"Service {service_name} not registered")
        return self._services[service_name]
    
    def start_all(self) -> None:
        """Start all registered services."""
        for service_name, service in self._services.items():
            try:
                logger.info(f"Starting service: {service_name}")
                service.start()
            except Exception as e:
                logger.error(f"Failed to start service {service_name}: {e}")
    
    def stop_all(self) -> None:
        """Stop all registered services."""
        for service_name, service in self._services.items():
            try:
                logger.info(f"Stopping service: {service_name}")
                service.stop()
            except Exception as e:
                logger.error(f"Failed to stop service {service_name}: {e}")
    
    def cleanup(self) -> None:
        """Clean up all services and reset the registry."""
        self.stop_all()
        self._services.clear()