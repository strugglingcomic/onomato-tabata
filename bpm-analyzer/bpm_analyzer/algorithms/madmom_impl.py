"""
madmom beat detection implementation
"""
from typing import Optional
import numpy as np

from bpm_analyzer.algorithms.base import BeatDetector
from bpm_analyzer.core.tempo_map import TempoMap, Beat
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class MadmomDetector(BeatDetector):
    """Beat detection using madmom library"""
    
    @property
    def name(self) -> str:
        return "madmom"
    
    @property
    def supports_variable_tempo(self) -> bool:
        return True
    
    @property
    def supports_downbeats(self) -> bool:
        return True
    
    def detect(self, audio_data: AudioData) -> TempoMap:
        """
        Detect beats using madmom's DBNBeatTracker.
        
        This uses a Dynamic Bayesian Network trained on multiple datasets
        for high-accuracy beat tracking.
        """
        logger.info(f"Running madmom beat detection on {audio_data.duration:.1f}s audio")
        
        try:
            import madmom
        except ImportError:
            raise ImportError(
                "madmom is not installed. Install with: pip install madmom"
            )
        
        # Create madmom beat processor
        proc = madmom.features.beats.DBNBeatTrackingProcessor(fps=100)
        
        # RNN beat activation function processor  
        act_proc = madmom.features.beats.RNNBeatProcessor()
        
        # Process audio to get activation function
        activations = act_proc(audio_data.audio)
        
        # Track beats using DBN
        beat_times = proc(activations)
        
        logger.info(f"Detected {len(beat_times)} beats")
        
        return self._create_tempo_map(beat_times, audio_data)
    
    def _create_tempo_map(
        self, 
        beat_times: np.ndarray,
        audio_data: AudioData,
        downbeat_times: Optional[np.ndarray] = None
    ) -> TempoMap:
        """Create TempoMap from madmom output"""
        beats = []
        for i, time in enumerate(beat_times):
            beats.append(
                Beat(
                    time=float(time),
                    position=(i % 4) + 1,  # Assume 4/4 time
                    confidence=0.9  # madmom doesn't provide per-beat confidence
                )
            )
        
        # Calculate average BPM
        if len(beat_times) > 1:
            intervals = np.diff(beat_times)
            avg_bpm = 60.0 / np.mean(intervals)
        else:
            avg_bpm = 120.0  # Default
        
        return TempoMap(
            beats=beats,
            average_bpm=float(avg_bpm),
            downbeats=downbeat_times.tolist() if downbeat_times is not None else None,
        )
