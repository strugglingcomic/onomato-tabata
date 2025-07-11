"""
aubio beat detection implementation
"""
from bpm_analyzer.algorithms.base import BeatDetector
from bpm_analyzer.core.tempo_map import TempoMap, Beat
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class AubioDetector(BeatDetector):
    """Beat detection using aubio library"""
    
    @property
    def name(self) -> str:
        return "aubio"
    
    def detect(self, audio_data: AudioData) -> TempoMap:
        """
        Detect beats using aubio's tempo detection.
        """
        logger.info(f"Running aubio beat detection on {audio_data.duration:.1f}s audio")
        
        try:
            import aubio
        except ImportError:
            raise ImportError(
                "aubio is not installed. Install with: pip install aubio"
            )
        
        # TODO: Implement aubio beat detection
        # 1. Use aubio.tempo
        # 2. Process audio in chunks
        # 3. Create TempoMap
        
        raise NotImplementedError("aubio beat detection not yet implemented")
