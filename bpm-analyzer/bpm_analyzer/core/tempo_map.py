"""
Tempo map data structures
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class Beat:
    """Single beat annotation"""
    time: float  # Time in seconds
    position: int  # Beat position within measure (1, 2, 3, 4, etc.)
    confidence: float = 1.0  # Confidence score [0, 1]
    
    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if self.time < 0:
            raise ValueError(f"Beat time cannot be negative, got {self.time}")
        if self.position < 1:
            raise ValueError(f"Beat position must be >= 1, got {self.position}")


@dataclass
class TempoMap:
    """Container for tempo and beat information"""
    
    # Beat information
    beats: List[Beat]
    
    # Tempo information
    average_bpm: float
    tempo_curve: Optional[np.ndarray] = None  # Time-varying tempo
    tempo_confidence: Optional[np.ndarray] = None  # Confidence for tempo curve
    
    # Downbeat information
    downbeats: Optional[List[float]] = None  # Times of downbeats (position 1)
    
    # Time signature information
    time_signature: Optional[Tuple[int, int]] = None  # e.g., (4, 4)
    
    def __post_init__(self):
        """Validate tempo map"""
        if not self.beats:
            raise ValueError("TempoMap must contain at least one beat")
        
        # Ensure beats are sorted by time
        self.beats = sorted(self.beats, key=lambda b: b.time)
        
        # Validate tempo curve dimensions
        if self.tempo_curve is not None and self.tempo_confidence is not None:
            if len(self.tempo_curve) != len(self.tempo_confidence):
                raise ValueError("tempo_curve and tempo_confidence must have same length")
    
    @property
    def duration(self) -> float:
        """Get duration covered by tempo map"""
        return self.beats[-1].time if self.beats else 0.0
    
    @property
    def beat_times(self) -> np.ndarray:
        """Get array of beat times"""
        return np.array([beat.time for beat in self.beats])
    
    @property
    def beat_intervals(self) -> np.ndarray:
        """Get intervals between consecutive beats"""
        times = self.beat_times
        return np.diff(times) if len(times) > 1 else np.array([])
    
    @property
    def instantaneous_bpm(self) -> np.ndarray:
        """Calculate instantaneous BPM from beat intervals"""
        intervals = self.beat_intervals
        return 60.0 / intervals if len(intervals) > 0 else np.array([])
    
    def get_tempo_at_time(self, time: float) -> float:
        """Get tempo at specific time"""
        if self.tempo_curve is None:
            return self.average_bpm
        
        # Assuming 10Hz tempo curve (0.1s resolution)
        idx = int(time * 10)
        if idx >= len(self.tempo_curve):
            return self.tempo_curve[-1]
        return self.tempo_curve[idx]
    
    def get_beats_in_range(self, start_time: float, end_time: float) -> List[Beat]:
        """Get beats within time range"""
        return [
            beat for beat in self.beats
            if start_time <= beat.time <= end_time
        ]
    
    def filter_by_confidence(self, min_confidence: float) -> "TempoMap":
        """Create new TempoMap with only high-confidence beats"""
        filtered_beats = [
            beat for beat in self.beats
            if beat.confidence >= min_confidence
        ]
        
        if not filtered_beats:
            raise ValueError(f"No beats with confidence >= {min_confidence}")
        
        # Recalculate average BPM from filtered beats
        if len(filtered_beats) > 1:
            intervals = np.diff([b.time for b in filtered_beats])
            filtered_bpm = float(np.mean(60.0 / intervals))
        else:
            filtered_bpm = self.average_bpm
        
        return TempoMap(
            beats=filtered_beats,
            average_bpm=filtered_bpm,
            tempo_curve=self.tempo_curve,
            tempo_confidence=self.tempo_confidence,
            downbeats=self.downbeats,
            time_signature=self.time_signature,
        )
    
    def quantize_to_grid(self, grid_size: float = 0.01) -> "TempoMap":
        """Quantize beat times to nearest grid point"""
        quantized_beats = []
        
        for beat in self.beats:
            quantized_time = round(beat.time / grid_size) * grid_size
            quantized_beats.append(
                Beat(
                    time=quantized_time,
                    position=beat.position,
                    confidence=beat.confidence
                )
            )
        
        return TempoMap(
            beats=quantized_beats,
            average_bpm=self.average_bpm,
            tempo_curve=self.tempo_curve,
            tempo_confidence=self.tempo_confidence,
            downbeats=self.downbeats,
            time_signature=self.time_signature,
        )
    
    def merge_with(self, other: "TempoMap", weight: float = 0.5) -> "TempoMap":
        """Merge with another tempo map using weighted average"""
        if not 0 <= weight <= 1:
            raise ValueError("Weight must be between 0 and 1")
        
        # Merge beats by finding closest matches
        merged_beats = []
        used_other = set()
        
        for beat in self.beats:
            # Find closest beat in other
            other_times = np.array([b.time for b in other.beats])
            distances = np.abs(other_times - beat.time)
            closest_idx = np.argmin(distances)
            
            if distances[closest_idx] < 0.05:  # Within 50ms
                # Merge the beats
                other_beat = other.beats[closest_idx]
                merged_time = beat.time * weight + other_beat.time * (1 - weight)
                merged_confidence = beat.confidence * weight + other_beat.confidence * (1 - weight)
                
                merged_beats.append(
                    Beat(
                        time=merged_time,
                        position=beat.position,
                        confidence=merged_confidence
                    )
                )
                used_other.add(closest_idx)
            else:
                # Keep original beat with reduced confidence
                merged_beats.append(
                    Beat(
                        time=beat.time,
                        position=beat.position,
                        confidence=beat.confidence * weight
                    )
                )
        
        # Add remaining beats from other
        for i, beat in enumerate(other.beats):
            if i not in used_other:
                merged_beats.append(
                    Beat(
                        time=beat.time,
                        position=beat.position,
                        confidence=beat.confidence * (1 - weight)
                    )
                )
        
        # Sort by time
        merged_beats = sorted(merged_beats, key=lambda b: b.time)
        
        # Merge BPM
        merged_bpm = self.average_bpm * weight + other.average_bpm * (1 - weight)
        
        return TempoMap(
            beats=merged_beats,
            average_bpm=merged_bpm,
            tempo_curve=None,  # TODO: Implement tempo curve merging
            tempo_confidence=None,
            downbeats=None,  # TODO: Implement downbeat merging
            time_signature=self.time_signature,
        )
