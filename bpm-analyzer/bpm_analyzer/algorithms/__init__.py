"""
Beat detection algorithms
"""
from bpm_analyzer.algorithms.base import BeatDetector, AlgorithmResult
from bpm_analyzer.algorithms.madmom_impl import MadmomDetector
from bpm_analyzer.algorithms.essentia_impl import EssentiaDetector
from bpm_analyzer.algorithms.librosa_impl import LibrosaDetector
from bpm_analyzer.algorithms.aubio_impl import AubioDetector
from bpm_analyzer.algorithms.ensemble import EnsembleDetector

__all__ = [
    "BeatDetector",
    "AlgorithmResult",
    "MadmomDetector",
    "EssentiaDetector",
    "LibrosaDetector",
    "AubioDetector",
    "EnsembleDetector",
]
