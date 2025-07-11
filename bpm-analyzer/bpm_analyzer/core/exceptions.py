"""
Custom exceptions for BPM Analyzer
"""


class BPMAnalyzerError(Exception):
    """Base exception for all BPM Analyzer errors"""
    pass


class AudioLoadError(BPMAnalyzerError):
    """Error loading audio file"""
    pass


class AnalysisError(BPMAnalyzerError):
    """Error during audio analysis"""
    pass


class ConfigurationError(BPMAnalyzerError):
    """Error in configuration"""
    pass


class AlgorithmError(AnalysisError):
    """Error in beat detection algorithm"""
    pass


class UnsupportedFormatError(AudioLoadError):
    """Audio format not supported"""
    pass


class CorruptedFileError(AudioLoadError):
    """Audio file is corrupted or unreadable"""
    pass


class DatabaseError(BPMAnalyzerError):
    """Error in database operations"""
    pass


class ValidationError(BPMAnalyzerError):
    """Error in input validation"""
    pass
