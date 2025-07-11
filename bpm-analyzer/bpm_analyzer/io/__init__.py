"""
Audio file loading module
"""
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
import numpy as np

from bpm_analyzer.core.exceptions import AudioLoadError, UnsupportedFormatError


@dataclass
class AudioData:
    """Container for loaded audio data"""
    audio: np.ndarray  # Audio samples
    sample_rate: int
    duration: float
    channels: int = 1
    
    @property
    def samples(self) -> int:
        """Total number of samples"""
        return len(self.audio)


def load_audio(
    file_path: Union[str, Path],
    sr: Optional[int] = None,
    mono: bool = True,
    offset: float = 0.0,
    duration: Optional[float] = None,
) -> AudioData:
    """
    Load audio file with automatic format detection.
    
    Args:
        file_path: Path to audio file
        sr: Target sample rate (None = use file's rate)
        mono: Convert to mono
        offset: Start reading at this time (seconds)
        duration: Only read this many seconds
        
    Returns:
        AudioData object containing audio and metadata
        
    Raises:
        AudioLoadError: If file cannot be loaded
        UnsupportedFormatError: If format is not supported
    """
    # TODO: Implement audio loading
    # 1. Try soundfile first (fast for WAV/FLAC)
    # 2. Fall back to pydub for MP3/other formats
    # 3. Normalize to float32 [-1, 1]
    # 4. Resample if needed
    # 5. Convert to mono if requested
    
    raise NotImplementedError("Audio loading not yet implemented")
