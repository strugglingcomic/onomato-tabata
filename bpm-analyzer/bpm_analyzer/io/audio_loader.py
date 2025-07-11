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
    import librosa
    import soundfile as sf
    from pydub import AudioSegment
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise AudioLoadError(f"File not found: {file_path}")
    
    try:
        # Try librosa first (handles most formats including MP3)
        y, sample_rate = librosa.load(
            str(file_path),
            sr=sr,
            mono=mono,
            offset=offset,
            duration=duration
        )
        
        # Ensure float32 and proper range
        y = y.astype(np.float32)
        if y.max() > 1.0 or y.min() < -1.0:
            y = librosa.util.normalize(y)
        
        audio_duration = len(y) / sample_rate
        channels = 1 if mono else (2 if y.ndim > 1 else 1)
        
        return AudioData(
            audio=y,
            sample_rate=sample_rate,
            duration=audio_duration,
            channels=channels
        )
        
    except Exception as e:
        raise AudioLoadError(f"Failed to load audio file {file_path}: {str(e)}")
