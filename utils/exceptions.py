"""Custom exceptions for the Dek0nstruct application."""

class VideoSplitterError(Exception):
    """Base exception class for Dek0nstruct."""
    pass

class ServiceError(VideoSplitterError):
    """Base exception for service-related errors."""
    pass

class ConfigurationError(VideoSplitterError):
    """Error raised when there's a configuration issue."""
    pass

class ResourceError(VideoSplitterError):
    """Error raised when a required resource is unavailable."""
    pass

class JobError(VideoSplitterError):
    """Error raised when there's an issue with a background job."""
    pass

class ValidationError(VideoSplitterError):
    """Error raised when input validation fails."""
    pass

class AIError(VideoSplitterError):
    """Error raised when an AI operation fails."""
    pass

class AudioError(VideoSplitterError):
    """Error raised when an audio operation fails."""
    pass

class CacheError(VideoSplitterError):
    """Error raised when there's an issue with the media cache."""
    pass