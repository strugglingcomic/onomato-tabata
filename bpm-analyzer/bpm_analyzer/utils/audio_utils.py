"""
Audio processing utilities
"""
import numpy as np
import librosa
from typing import Tuple

def resample_audio(y: np.ndarray, sr: int, target_sr: int) -> Tuple[np.ndarray, int]:
    """Resample audio to target sample rate."""
    if sr == target_sr:
        return y, sr
    return librosa.resample(y, orig_sr=sr, target_sr=target_sr), target_sr

def normalize_audio(y: np.ndarray) -> np.ndarray:
    """Normalize audio to [-1, 1] range."""
    return librosa.util.normalize(y)

def convert_to_mono(y: np.ndarray) -> np.ndarray:
    """Convert stereo audio to mono."""
    if y.ndim > 1:
        return librosa.to_mono(y)
    return y