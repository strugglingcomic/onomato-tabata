"""
Base classes for beat detection algorithms
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

from bpm_analyzer.core.tempo_map import TempoMap
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.config import AnalysisConfig


@dataclass
class AlgorithmResult:
    """Result from a beat detection algorithm"""
    tempo_map: TempoMap
    metadata: Dict[str, Any]
    warnings: list[str]


class BeatDetector(ABC):
    """Abstract base class for beat detection algorithms"""
    
    def __init__(self, config: AnalysisConfig):
        """
        Initialize beat detector.
        
        Args:
            config: Analysis configuration
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration for this algorithm"""
        pass
    
    @abstractmethod
    def detect(self, audio_data: AudioData) -> TempoMap:
        """
        Detect beats in audio data.
        
        Args:
            audio_data: Loaded audio data
            
        Returns:
            TempoMap containing beat and tempo information
            
        Raises:
            AlgorithmError: If detection fails
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get algorithm name"""
        pass
    
    @property
    def supports_variable_tempo(self) -> bool:
        """Whether this algorithm supports variable tempo tracking"""
        return False
    
    @property
    def supports_downbeats(self) -> bool:
        """Whether this algorithm can detect downbeats"""
        return False
    
    def preprocess_audio(self, audio_data: AudioData) -> AudioData:
        """
        Preprocess audio before beat detection.
        
        Can be overridden by subclasses for algorithm-specific preprocessing.
        
        Args:
            audio_data: Input audio data
            
        Returns:
            Preprocessed audio data
        """
        return audio_data
    
    def postprocess_tempo_map(self, tempo_map: TempoMap) -> TempoMap:
        """
        Postprocess tempo map after detection.
        
        Can be overridden by subclasses for algorithm-specific postprocessing.
        
        Args:
            tempo_map: Initial tempo map
            
        Returns:
            Postprocessed tempo map
        """
        return tempo_map
