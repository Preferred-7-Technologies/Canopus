class CanopusError(Exception):
    """Base exception for Canopus client"""
    pass

class APIError(CanopusError):
    """Raised when API communication fails"""
    pass

class AuthenticationError(CanopusError):
    """Raised when authentication fails"""
    pass

class AudioProcessingError(CanopusError):
    """Raised when audio processing fails"""
    pass

class DatabaseError(CanopusError):
    """Raised when database operations fail"""
    pass
