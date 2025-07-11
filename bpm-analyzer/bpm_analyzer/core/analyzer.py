"""
Core analysis orchestration module
"""
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import numpy as np
import jams

from bpm_analyzer.config import AnalysisConfig, AlgorithmType
from bpm_analyzer.io.audio_loader import load_audio
from bpm_analyzer.algorithms.base import BeatDetector
from bpm_analyzer.algorithms import (
    MadmomDetector,
    EssentiaDetector,
    LibrosaDetector,
    AubioDetector,
    EnsembleDetector,
)
from bpm_analyzer.core.tempo_map import TempoMap, Beat
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    
    # File information
    file_path: Path
    duration: float
    sample_rate: int
    
    # Tempo information
    average_bpm: float
    tempo_curve: Optional[np.ndarray] = None
    tempo_confidence: Optional[np.ndarray] = None
    
    # Beat information
    beats: list[Beat] = field(default_factory=list)
    downbeats: Optional[list[float]] = None
    
    # Metadata
    algorithm: str = ""
    processing_time: float = 0.0
    warnings: list[str] = field(default_factory=list)
    
    @property
    def beat_times(self) -> np.ndarray:
        """Get array of beat times"""
        return np.array([beat.time for beat in self.beats])
    
    @property
    def beat_count(self) -> int:
        """Get total number of beats"""
        return len(self.beats)
    
    def to_jams(self) -> jams.JAMS:
        """Convert results to JAMS format"""
        jam = jams.JAMS()
        
        # Add file metadata
        jam.file_metadata.duration = self.duration
        jam.file_metadata.identifiers = {"file": str(self.file_path)}
        
        # Add tempo annotation
        tempo_ann = jams.Annotation(namespace='tempo')
        tempo_ann.annotation_metadata = jams.AnnotationMetadata(
            curator=jams.Curator(name='bpm_analyzer'),
            data_source=self.algorithm
        )
        
        if self.tempo_curve is not None:
            # Time-varying tempo
            for i, (tempo, confidence) in enumerate(zip(self.tempo_curve, self.tempo_confidence)):
                tempo_ann.append(
                    time=i * 0.1,  # Assuming 10Hz tempo curve
                    duration=0.1,
                    value=float(tempo),
                    confidence=float(confidence)
                )
        else:
            # Single tempo value
            tempo_ann.append(
                time=0.0,
                duration=self.duration,
                value=self.average_bpm,
                confidence=1.0
            )
        
        jam.annotations.append(tempo_ann)
        
        # Add beat annotation
        beat_ann = jams.Annotation(namespace='beat')
        beat_ann.annotation_metadata = jams.AnnotationMetadata(
            curator=jams.Curator(name='bpm_analyzer'),
            data_source=self.algorithm
        )
        
        for beat in self.beats:
            beat_ann.append(
                time=beat.time,
                duration=0.0,
                value=beat.position,
                confidence=beat.confidence
            )
        
        jam.annotations.append(beat_ann)
        
        # Add downbeat annotation if available
        if self.downbeats:
            downbeat_ann = jams.Annotation(namespace='beat')
            downbeat_ann.annotation_metadata = jams.AnnotationMetadata(
                curator=jams.Curator(name='bpm_analyzer'),
                data_source=self.algorithm,
                annotator={'bibtex': 'downbeat_detector'}
            )
            
            for i, time in enumerate(self.downbeats):
                downbeat_ann.append(
                    time=time,
                    duration=0.0,
                    value=1,  # Downbeats are always position 1
                    confidence=1.0
                )
            
            jam.annotations.append(downbeat_ann)
        
        return jam
    
    def save(self, output_path: Path, format: str = "jams") -> None:
        """Save results to file"""
        output_path = Path(output_path)
        
        if format == "jams":
            jam = self.to_jams()
            jam.save(str(output_path))
        elif format == "csv":
            self._save_csv(output_path)
        elif format == "json":
            self._save_json(output_path)
        else:
            raise ValueError(f"Unsupported output format: {format}")
    
    def _save_csv(self, output_path: Path) -> None:
        """Save results as CSV"""
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time', 'position', 'confidence', 'bpm'])
            
            for i, beat in enumerate(self.beats):
                if i > 0:
                    # Calculate instantaneous BPM
                    bpm = 60.0 / (beat.time - self.beats[i-1].time)
                else:
                    bpm = self.average_bpm
                writer.writerow([beat.time, beat.position, beat.confidence, bpm])
    
    def _save_json(self, output_path: Path) -> None:
        """Save results as JSON"""
        import json
        
        data = {
            'file': str(self.file_path),
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'average_bpm': self.average_bpm,
            'algorithm': self.algorithm,
            'processing_time': self.processing_time,
            'beats': [
                {
                    'time': beat.time,
                    'position': beat.position,
                    'confidence': beat.confidence
                }
                for beat in self.beats
            ]
        }
        
        if self.downbeats:
            data['downbeats'] = self.downbeats
        
        if self.tempo_curve is not None:
            data['tempo_curve'] = self.tempo_curve.tolist()
            data['tempo_confidence'] = self.tempo_confidence.tolist()
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


class AudioAnalyzer:
    """Main analyzer class that orchestrates the analysis process"""
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self._detectors: Dict[str, BeatDetector] = {}
        self._init_detectors()
    
    def _init_detectors(self) -> None:
        """Initialize beat detection algorithms"""
        # Lazy initialization of detectors
        self._detector_classes = {
            AlgorithmType.MADMOM: MadmomDetector,
            AlgorithmType.ESSENTIA: EssentiaDetector,
            AlgorithmType.LIBROSA: LibrosaDetector,
            AlgorithmType.AUBIO: AubioDetector,
            AlgorithmType.ENSEMBLE: EnsembleDetector,
        }
    
    def _get_detector(self, algorithm: str) -> BeatDetector:
        """Get or create a detector instance"""
        if algorithm not in self._detectors:
            detector_class = self._detector_classes.get(algorithm)
            if detector_class is None:
                raise ValueError(f"Unknown algorithm: {algorithm}")
            self._detectors[algorithm] = detector_class(self.config)
        return self._detectors[algorithm]
    
    def analyze(self, audio_path: Path) -> AnalysisResult:
        """Analyze an audio file"""
        import time
        start_time = time.time()
        
        logger.info(f"Analyzing {audio_path} with {self.config.algorithm}")
        
        # Load audio
        try:
            audio_data = load_audio(
                audio_path,
                sr=self.config.sample_rate,
                mono=True
            )
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise
        
        # Get detector
        detector = self._get_detector(self.config.algorithm)
        
        # Detect beats
        tempo_map = detector.detect(audio_data)
        
        # Filter by confidence if threshold is set
        if self.config.confidence_threshold > 0:
            tempo_map = tempo_map.filter_by_confidence(self.config.confidence_threshold)
        
        # Create result
        result = AnalysisResult(
            file_path=audio_path,
            duration=audio_data.duration,
            sample_rate=audio_data.sample_rate,
            average_bpm=tempo_map.average_bpm,
            tempo_curve=tempo_map.tempo_curve,
            tempo_confidence=tempo_map.tempo_confidence,
            beats=tempo_map.beats,
            downbeats=tempo_map.downbeats,
            algorithm=self.config.algorithm,
            processing_time=time.time() - start_time,
        )
        
        logger.info(
            f"Analysis complete: {len(result.beats)} beats detected, "
            f"average BPM: {result.average_bpm:.1f}, "
            f"processing time: {result.processing_time:.2f}s"
        )
        
        return result


def analyze_file(
    audio_path: Path,
    config: Optional[AnalysisConfig] = None
) -> AnalysisResult:
    """Convenience function to analyze a single file"""
    analyzer = AudioAnalyzer(config)
    return analyzer.analyze(audio_path)
