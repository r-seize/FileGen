"""
Custom exceptions
"""

class FileGenError(Exception):
    pass

class ParsingError(FileGenError):
    pass

class ValidationError(FileGenError):
    pass

class GenerationError(FileGenError):
    pass

class ConfigurationError(FileGenError):
    pass