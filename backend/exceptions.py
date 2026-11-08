"""
Custom exception classes for the Multimodal Image Classifier application.
"""


class ApplicationError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize application error.
        
        Args:
            message: Error message
            status_code: HTTP status code
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(ApplicationError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AuthenticationError(ApplicationError):
    """Raised when API key authentication fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class ModelNotFoundError(ApplicationError):
    """Raised when a model is not found."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ModelDownloadError(ApplicationError):
    """Raised when model download fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class ClassificationError(ApplicationError):
    """Raised when classification fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class ImageLoadError(ApplicationError):
    """Raised when image loading fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class EvaluationError(ApplicationError):
    """Raised when evaluation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class StorageError(ApplicationError):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
