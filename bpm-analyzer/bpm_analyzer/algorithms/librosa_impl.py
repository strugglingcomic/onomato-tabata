"""
librosa beat detection implementation
"""
from bpm_analyzer.algorithms.base import BeatDetector
from bpm_analyzer.core.tempo_map import TempoMap, Beat
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class LibrosaDetector(BeatDetector):
    """Beat detection using librosa library"""
    
    @property
    def name(self) -> str:
        return "librosa"
    
    def detect(self, audio_data: AudioData) -> TempoMap:
        """
        Detect beats using librosa's beat tracking.
        """
        logger.info(f"Running librosa beat detection on {audio_data.duration:.1f}s audio")
        
        try:
            import librosa
        except ImportError:
            raise ImportError(
                "librosa is not installed. Install with: pip install librosa"
            )
        
        # Use librosa's beat tracking
        tempo, beat_frames = librosa.beat.beat_track(
            y=audio_data.audio,
            sr=audio_data.sample_rate,
            hop_length=512
        )
        
        # Convert beat frames to time
        beat_times = librosa.frames_to_time(beat_frames, sr=audio_data.sample_rate, hop_length=512)
        
        logger.info(f"Detected tempo: {float(tempo):.1f} BPM, {len(beat_times)} beats")
        
        # Create beats list
        beats = []
        for i, time in enumerate(beat_times):
            beats.append(
                Beat(
                    time=float(time),
                    position=(i % 4) + 1,  # Assume 4/4 time
                    confidence=0.8  # librosa doesn't provide per-beat confidence
                )
            )
        
        return TempoMap(
            beats=beats,
            average_bpm=float(tempo),
            downbeats=None,
        )
