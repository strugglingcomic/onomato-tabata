"""
BPM Analyzer - High-precision audio tempo analysis

A Python library and CLI tool for extracting beat-by-beat tempo information
from audio files, designed for applications requiring accurate tempo mapping.
"""

from bpm_analyzer.version import __version__
from bpm_analyzer.core.analyzer import analyze_file, AudioAnalyzer, AnalysisResult
from bpm_analyzer.config import AnalysisConfig, GlobalConfig
from bpm_analyzer.processors.batch import BatchProcessor
from bpm_analyzer.db.database import AnalysisDB

__all__ = [
    "__version__",
    "analyze_file",
    "AudioAnalyzer",
    "AnalysisResult",
    "AnalysisConfig",
    "GlobalConfig",
    "BatchProcessor",
    "AnalysisDB",
]

# Convenience function
def analyze_audio(audio_path, **kwargs):
    """
    Convenience function to analyze an audio file.
    
    Args:
        audio_path: Path to audio file
        **kwargs: Additional arguments for AnalysisConfig
        
    Returns:
        AnalysisResult object
    """
    config = AnalysisConfig(**kwargs)
    return analyze_file(audio_path, config)
