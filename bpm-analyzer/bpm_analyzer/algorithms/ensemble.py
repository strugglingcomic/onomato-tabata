"""
Ensemble beat detection combining multiple algorithms
"""
from typing import List, Dict, Tuple
import numpy as np

from bpm_analyzer.algorithms.base import BeatDetector
from bpm_analyzer.core.tempo_map import TempoMap
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class EnsembleDetector(BeatDetector):
    """Combine multiple beat detection algorithms"""
    
    def __init__(self, config):
        super().__init__(config)
        self.detectors: List[BeatDetector] = []
        self._init_detectors()
    
    def _init_detectors(self) -> None:
        """Initialize component detectors"""
        # Import here to avoid circular imports
        from bpm_analyzer.algorithms import (
            MadmomDetector,
            EssentiaDetector,
            LibrosaDetector,
        )
        
        detector_classes = {
            "madmom": MadmomDetector,
            "essentia": EssentiaDetector,
            "librosa": LibrosaDetector,
        }
        
        for algo_name in self.config.ensemble_algorithms:
            if algo_name in detector_classes:
                detector_class = detector_classes[algo_name]
                self.detectors.append(detector_class(self.config))
    
    @property
    def name(self) -> str:
        return "ensemble"
    
    @property
    def supports_variable_tempo(self) -> bool:
        return any(d.supports_variable_tempo for d in self.detectors)
    
    @property
    def supports_downbeats(self) -> bool:
        return any(d.supports_downbeats for d in self.detectors)
    
    def detect(self, audio_data: AudioData) -> TempoMap:
        """
        Detect beats using ensemble of algorithms.
        """
        if not self.detectors:
            raise ValueError("No detectors configured for ensemble")
        
        logger.info(
            f"Running ensemble beat detection with {len(self.detectors)} algorithms"
        )
        
        # Collect results from all detectors
        results: List[Tuple[TempoMap, float]] = []
        
        for detector in self.detectors:
            try:
                tempo_map = detector.detect(audio_data)
                weight = self._get_detector_weight(detector)
                results.append((tempo_map, weight))
                logger.info(f"{detector.name} completed with weight {weight}")
            except Exception as e:
                logger.warning(f"{detector.name} failed: {e}")
        
        if not results:
            raise RuntimeError("All detectors failed")
        
        # Combine results
        return self._combine_results(results)
    
    def _get_detector_weight(self, detector: BeatDetector) -> float:
        """Get weight for detector in ensemble"""
        # Could be configurable, for now use equal weights
        weights = {
            "madmom": 1.0,
            "essentia": 0.8,
            "librosa": 0.6,
            "aubio": 0.5,
        }
        return weights.get(detector.name, 0.5)
    
    def _combine_results(
        self, 
        results: List[Tuple[TempoMap, float]]
    ) -> TempoMap:
        """Combine multiple tempo maps into one"""
        if len(results) == 1:
            return results[0][0]
        
        # Start with the highest weighted result
        results.sort(key=lambda x: x[1], reverse=True)
        combined = results[0][0]
        
        # Merge with other results
        total_weight = results[0][1]
        for tempo_map, weight in results[1:]:
            # Calculate relative weight
            rel_weight = weight / (total_weight + weight)
            combined = combined.merge_with(tempo_map, weight=1 - rel_weight)
            total_weight += weight
        
        return combined
