"""
Input validation utilities
"""
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

import soundfile as sf

from bpm_analyzer.core.exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of audio file validation"""
    is_valid: bool
    error: Optional[str] = None
    format: Optional[str] = None
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


def validate_audio_file(file_path: Path) -> ValidationResult:
    """
    Validate an audio file.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        ValidationResult with file information
    """
    if not file_path.exists():
        return ValidationResult(
            is_valid=False,
            error=f"File not found: {file_path}"
        )
    
    if not file_path.is_file():
        return ValidationResult(
            is_valid=False,
            error=f"Not a file: {file_path}"
        )
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size == 0:
        return ValidationResult(
            is_valid=False,
            error="File is empty"
        )
    
    if file_size > 1e9:  # 1GB limit
        return ValidationResult(
            is_valid=False,
            error=f"File too large: {file_size / 1e9:.1f}GB"
        )
    
    # Try to read file info
    try:
        info = sf.info(str(file_path))
        
        return ValidationResult(
            is_valid=True,
            format=info.format,
            duration=info.duration,
            sample_rate=info.samplerate,
            channels=info.channels,
        )
    except Exception as e:
        # Try with pydub as fallback
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(file_path))
            
            return ValidationResult(
                is_valid=True,
                format=file_path.suffix[1:],
                duration=len(audio) / 1000.0,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
            )
        except Exception as e2:
            return ValidationResult(
                is_valid=False,
                error=f"Cannot read audio file: {str(e)}"
            )


def validate_tempo_range(tempo_range: Tuple[float, float]) -> None:
    """
    Validate tempo range.
    
    Args:
        tempo_range: (min_bpm, max_bpm) tuple
        
    Raises:
        ValidationError: If tempo range is invalid
    """
    min_bpm, max_bpm = tempo_range
    
    if min_bpm <= 0:
        raise ValidationError(f"Minimum BPM must be positive, got {min_bpm}")
    
    if max_bpm <= min_bpm:
        raise ValidationError(
            f"Maximum BPM ({max_bpm}) must be greater than minimum ({min_bpm})"
        )
    
    if min_bpm < 20:
        raise ValidationError(f"Minimum BPM too low: {min_bpm} (must be >= 20)")
    
    if max_bpm > 500:
        raise ValidationError(f"Maximum BPM too high: {max_bpm} (must be <= 500)")


def validate_confidence(confidence: float) -> None:
    """
    Validate confidence value.
    
    Args:
        confidence: Confidence value to validate
        
    Raises:
        ValidationError: If confidence is invalid
    """
    if not 0 <= confidence <= 1:
        raise ValidationError(
            f"Confidence must be between 0 and 1, got {confidence}"
        )
