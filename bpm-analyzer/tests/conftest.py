import pytest
import numpy as np
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch
import tempfile
import os

from bpm_analyzer.core.tempo_map import TempoMap, Beat
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.config import AnalysisConfig
from bpm_analyzer.core.analyzer import AnalysisResult
from bpm_analyzer.db.database import AnalysisDB


@pytest.fixture
def sample_audio_data() -> AudioData:
    """Create sample audio data for testing"""
    duration = 10.0  # 10 seconds
    sample_rate = 44100
    audio = np.random.randn(int(duration * sample_rate)).astype(np.float32)
    
    return AudioData(
        audio=audio,
        sample_rate=sample_rate,
        duration=duration,
        channels=1
    )


@pytest.fixture
def sample_beats() -> list[Beat]:
    """Create sample beats for testing"""
    return [
        Beat(time=0.5, position=1, confidence=0.9),
        Beat(time=1.0, position=2, confidence=0.8),
        Beat(time=1.5, position=3, confidence=0.85),
        Beat(time=2.0, position=4, confidence=0.95),
        Beat(time=2.5, position=1, confidence=0.9),
        Beat(time=3.0, position=2, confidence=0.8),
    ]


@pytest.fixture
def sample_tempo_map(sample_beats) -> TempoMap:
    """Create sample tempo map for testing"""
    return TempoMap(
        beats=sample_beats,
        average_bpm=120.0,
        downbeats=[0.5, 2.5],
        tempo_curve=np.array([120.0, 121.0, 119.0, 120.0]),
        tempo_confidence=np.array([0.9, 0.8, 0.85, 0.9])
    )


@pytest.fixture
def sample_analysis_config() -> AnalysisConfig:
    """Create sample analysis configuration"""
    return AnalysisConfig(
        algorithm="librosa",
        sample_rate=44100,
        confidence_threshold=0.5,
        tempo_range=(60, 200),
        verbose=False
    )


@pytest.fixture
def temp_audio_file() -> Generator[Path, None, None]:
    """Create temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Create a simple sine wave
        import soundfile as sf
        
        duration = 5.0  # 5 seconds
        sample_rate = 44100
        frequency = 440.0  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * frequency * t)
        
        sf.write(f.name, audio, sample_rate)
        
        yield Path(f.name)
        
        # Cleanup
        os.unlink(f.name)


@pytest.fixture
def sample_analysis_result(temp_audio_file, sample_beats) -> AnalysisResult:
    """Create sample analysis result for testing"""
    return AnalysisResult(
        file_path=temp_audio_file,
        duration=5.0,
        sample_rate=44100,
        average_bpm=120.0,
        beats=sample_beats,
        algorithm="librosa",
        processing_time=1.5,
        warnings=[]
    )


@pytest.fixture
def temp_db() -> Generator[AnalysisDB, None, None]:
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_url = f"sqlite:///{f.name}"
        db = AnalysisDB(db_url)
        db.init_db()
        
        yield db
        
        # Cleanup
        os.unlink(f.name)


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Create temporary output directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_librosa():
    """Mock librosa for testing without actual audio processing"""
    with patch('librosa.beat.beat_track') as mock_beat_track, \
         patch('librosa.frames_to_time') as mock_frames_to_time:
        
        # Mock return values
        mock_beat_track.return_value = (120.0, np.array([10, 20, 30, 40]))
        mock_frames_to_time.return_value = np.array([0.5, 1.0, 1.5, 2.0])
        
        yield {
            'beat_track': mock_beat_track,
            'frames_to_time': mock_frames_to_time
        }


@pytest.fixture
def mock_audio_loader():
    """Mock audio loader for testing"""
    with patch('bpm_analyzer.io.audio_loader.load_audio') as mock_load:
        mock_load.return_value = AudioData(
            audio=np.random.randn(44100 * 5).astype(np.float32),
            sample_rate=44100,
            duration=5.0,
            channels=1
        )
        yield mock_load


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests"""
    import logging
    logging.basicConfig(level=logging.WARNING)
    yield
    # Reset logging after test
    logging.getLogger().handlers.clear()
