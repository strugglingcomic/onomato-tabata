import pytest
import numpy as np
from unittest.mock import Mock

from bpm_analyzer.core.tempo_map import Beat, TempoMap


class TestBeat:
    """Test Beat dataclass"""
    
    def test_init_valid(self):
        """Test valid Beat initialization"""
        beat = Beat(time=1.5, position=2, confidence=0.8)
        
        assert beat.time == 1.5
        assert beat.position == 2
        assert beat.confidence == 0.8
    
    def test_init_default_confidence(self):
        """Test Beat initialization with default confidence"""
        beat = Beat(time=1.0, position=1)
        
        assert beat.time == 1.0
        assert beat.position == 1
        assert beat.confidence == 1.0
    
    def test_init_confidence_out_of_range(self):
        """Test Beat initialization with invalid confidence"""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Beat(time=1.0, position=1, confidence=1.5)
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Beat(time=1.0, position=1, confidence=-0.1)
    
    def test_init_negative_time(self):
        """Test Beat initialization with negative time"""
        with pytest.raises(ValueError, match="Beat time cannot be negative"):
            Beat(time=-1.0, position=1)
    
    def test_init_invalid_position(self):
        """Test Beat initialization with invalid position"""
        with pytest.raises(ValueError, match="Beat position must be >= 1"):
            Beat(time=1.0, position=0)
        
        with pytest.raises(ValueError, match="Beat position must be >= 1"):
            Beat(time=1.0, position=-1)
    
    def test_init_boundary_values(self):
        """Test Beat initialization with boundary values"""
        # Valid boundary values
        beat1 = Beat(time=0.0, position=1, confidence=0.0)
        beat2 = Beat(time=1000.0, position=100, confidence=1.0)
        
        assert beat1.time == 0.0
        assert beat1.position == 1
        assert beat1.confidence == 0.0
        
        assert beat2.time == 1000.0
        assert beat2.position == 100
        assert beat2.confidence == 1.0


class TestTempoMap:
    """Test TempoMap dataclass"""
    
    def test_init_valid(self, sample_beats):
        """Test valid TempoMap initialization"""
        tempo_map = TempoMap(
            beats=sample_beats,
            average_bpm=120.0,
            downbeats=[0.5, 2.5],
            time_signature=(4, 4)
        )
        
        assert tempo_map.beats == sample_beats
        assert tempo_map.average_bpm == 120.0
        assert tempo_map.downbeats == [0.5, 2.5]
        assert tempo_map.time_signature == (4, 4)
    
    def test_init_minimal(self, sample_beats):
        """Test TempoMap initialization with minimal parameters"""
        tempo_map = TempoMap(
            beats=sample_beats,
            average_bpm=120.0
        )
        
        assert tempo_map.beats == sample_beats
        assert tempo_map.average_bpm == 120.0
        assert tempo_map.tempo_curve is None
        assert tempo_map.tempo_confidence is None
        assert tempo_map.downbeats is None
        assert tempo_map.time_signature is None
    
    def test_init_with_tempo_curve(self, sample_beats):
        """Test TempoMap initialization with tempo curve"""
        tempo_curve = np.array([120.0, 121.0, 119.0, 120.0])
        tempo_confidence = np.array([0.9, 0.8, 0.85, 0.9])
        
        tempo_map = TempoMap(
            beats=sample_beats,
            average_bpm=120.0,
            tempo_curve=tempo_curve,
            tempo_confidence=tempo_confidence
        )
        
        np.testing.assert_array_equal(tempo_map.tempo_curve, tempo_curve)
        np.testing.assert_array_equal(tempo_map.tempo_confidence, tempo_confidence)
    
    def test_init_empty_beats(self):
        """Test TempoMap initialization with empty beats"""
        with pytest.raises(ValueError, match="TempoMap must contain at least one beat"):
            TempoMap(beats=[], average_bpm=120.0)
    
    def test_init_mismatched_tempo_curve_lengths(self, sample_beats):
        """Test TempoMap initialization with mismatched tempo curve lengths"""
        tempo_curve = np.array([120.0, 121.0, 119.0])
        tempo_confidence = np.array([0.9, 0.8])  # Different length
        
        with pytest.raises(ValueError, match="tempo_curve and tempo_confidence must have same length"):
            TempoMap(
                beats=sample_beats,
                average_bpm=120.0,
                tempo_curve=tempo_curve,
                tempo_confidence=tempo_confidence
            )
    
    def test_beats_sorted_by_time(self):
        """Test that beats are automatically sorted by time"""
        unsorted_beats = [
            Beat(time=2.0, position=1),
            Beat(time=0.5, position=2),
            Beat(time=1.5, position=3),
            Beat(time=1.0, position=4)
        ]
        
        tempo_map = TempoMap(beats=unsorted_beats, average_bpm=120.0)
        
        # Should be sorted by time
        expected_times = [0.5, 1.0, 1.5, 2.0]
        actual_times = [beat.time for beat in tempo_map.beats]
        assert actual_times == expected_times
    
    def test_duration_property(self, sample_beats):
        """Test duration property"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Duration should be the time of the last beat
        assert tempo_map.duration == 3.0  # Last beat time from sample_beats
    
    def test_duration_property_empty(self):
        """Test duration property with empty beats"""
        # This should raise an error during initialization
        with pytest.raises(ValueError):
            TempoMap(beats=[], average_bpm=120.0)
    
    def test_beat_times_property(self, sample_beats):
        """Test beat_times property"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        expected_times = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
        np.testing.assert_array_equal(tempo_map.beat_times, expected_times)
    
    def test_beat_intervals_property(self, sample_beats):
        """Test beat_intervals property"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        expected_intervals = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        np.testing.assert_array_equal(tempo_map.beat_intervals, expected_intervals)
    
    def test_beat_intervals_single_beat(self):
        """Test beat_intervals property with single beat"""
        beats = [Beat(time=1.0, position=1)]
        tempo_map = TempoMap(beats=beats, average_bpm=120.0)
        
        expected_intervals = np.array([])
        np.testing.assert_array_equal(tempo_map.beat_intervals, expected_intervals)
    
    def test_instantaneous_bpm_property(self, sample_beats):
        """Test instantaneous_bpm property"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # BPM = 60 / interval, with 0.5s intervals -> 120 BPM
        expected_bpm = np.array([120.0, 120.0, 120.0, 120.0, 120.0])
        np.testing.assert_array_equal(tempo_map.instantaneous_bpm, expected_bpm)
    
    def test_instantaneous_bpm_single_beat(self):
        """Test instantaneous_bpm property with single beat"""
        beats = [Beat(time=1.0, position=1)]
        tempo_map = TempoMap(beats=beats, average_bpm=120.0)
        
        expected_bpm = np.array([])
        np.testing.assert_array_equal(tempo_map.instantaneous_bpm, expected_bpm)
    
    def test_get_tempo_at_time_no_curve(self, sample_beats):
        """Test get_tempo_at_time without tempo curve"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Should return average BPM for any time
        assert tempo_map.get_tempo_at_time(0.0) == 120.0
        assert tempo_map.get_tempo_at_time(1.5) == 120.0
        assert tempo_map.get_tempo_at_time(10.0) == 120.0
    
    def test_get_tempo_at_time_with_curve(self, sample_beats):
        """Test get_tempo_at_time with tempo curve"""
        tempo_curve = np.array([120.0, 121.0, 119.0, 120.0])
        tempo_confidence = np.array([0.9, 0.8, 0.85, 0.9])
        
        tempo_map = TempoMap(
            beats=sample_beats,
            average_bpm=120.0,
            tempo_curve=tempo_curve,
            tempo_confidence=tempo_confidence
        )
        
        # Tempo curve is sampled at 10Hz (0.1s intervals)
        assert tempo_map.get_tempo_at_time(0.0) == 120.0  # Index 0
        assert tempo_map.get_tempo_at_time(0.1) == 121.0  # Index 1
        assert tempo_map.get_tempo_at_time(0.2) == 119.0  # Index 2
        assert tempo_map.get_tempo_at_time(0.3) == 120.0  # Index 3
        assert tempo_map.get_tempo_at_time(1.0) == 120.0  # Beyond array, returns last
    
    def test_get_beats_in_range(self, sample_beats):
        """Test get_beats_in_range method"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Get beats between 1.0 and 2.0 seconds
        beats_in_range = tempo_map.get_beats_in_range(1.0, 2.0)
        
        assert len(beats_in_range) == 3
        expected_times = [1.0, 1.5, 2.0]
        actual_times = [beat.time for beat in beats_in_range]
        assert actual_times == expected_times
    
    def test_get_beats_in_range_no_beats(self, sample_beats):
        """Test get_beats_in_range with no beats in range"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Get beats in range where no beats exist
        beats_in_range = tempo_map.get_beats_in_range(5.0, 10.0)
        
        assert len(beats_in_range) == 0
    
    def test_get_beats_in_range_all_beats(self, sample_beats):
        """Test get_beats_in_range with range covering all beats"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Get all beats
        beats_in_range = tempo_map.get_beats_in_range(0.0, 10.0)
        
        assert len(beats_in_range) == len(sample_beats)
        assert beats_in_range == sample_beats
    
    def test_filter_by_confidence(self, sample_beats):
        """Test filter_by_confidence method"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Filter by confidence >= 0.85
        filtered = tempo_map.filter_by_confidence(0.85)
        
        # Should keep beats with confidence >= 0.85
        expected_count = len([b for b in sample_beats if b.confidence >= 0.85])
        assert len(filtered.beats) == expected_count
        
        # All remaining beats should have confidence >= 0.85
        for beat in filtered.beats:
            assert beat.confidence >= 0.85
    
    def test_filter_by_confidence_no_beats(self, sample_beats):
        """Test filter_by_confidence with no beats meeting criteria"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Filter by very high confidence
        with pytest.raises(ValueError, match="No beats with confidence"):
            tempo_map.filter_by_confidence(0.99)
    
    def test_filter_by_confidence_recalculates_bpm(self):
        """Test that filter_by_confidence recalculates average BPM"""
        beats = [
            Beat(time=0.0, position=1, confidence=0.9),
            Beat(time=0.5, position=2, confidence=0.7),  # Will be filtered out
            Beat(time=1.0, position=3, confidence=0.9),
        ]
        tempo_map = TempoMap(beats=beats, average_bpm=120.0)
        
        # Filter by confidence >= 0.85
        filtered = tempo_map.filter_by_confidence(0.85)
        
        # Should have 2 beats with 1.0s interval -> 60 BPM
        assert len(filtered.beats) == 2
        assert filtered.average_bpm == 60.0
    
    def test_filter_by_confidence_single_beat(self):
        """Test filter_by_confidence with single remaining beat"""
        beats = [
            Beat(time=0.0, position=1, confidence=0.9),
            Beat(time=0.5, position=2, confidence=0.7),  # Will be filtered out
        ]
        tempo_map = TempoMap(beats=beats, average_bpm=120.0)
        
        # Filter by confidence >= 0.85
        filtered = tempo_map.filter_by_confidence(0.85)
        
        # Should have 1 beat, BPM should remain original
        assert len(filtered.beats) == 1
        assert filtered.average_bpm == 120.0
    
    def test_quantize_to_grid(self, sample_beats):
        """Test quantize_to_grid method"""
        tempo_map = TempoMap(beats=sample_beats, average_bpm=120.0)
        
        # Quantize to 0.1s grid
        quantized = tempo_map.quantize_to_grid(0.1)
        
        # All beat times should be multiples of 0.1
        for beat in quantized.beats:
            assert beat.time % 0.1 == 0.0
    
    def test_quantize_to_grid_custom_size(self):
        """Test quantize_to_grid with custom grid size"""
        beats = [
            Beat(time=0.53, position=1),
            Beat(time=1.27, position=2),
            Beat(time=2.81, position=3),
        ]
        tempo_map = TempoMap(beats=beats, average_bpm=120.0)
        
        # Quantize to 0.25s grid
        quantized = tempo_map.quantize_to_grid(0.25)
        
        # Check quantized times
        expected_times = [0.5, 1.25, 2.75]  # Rounded to nearest 0.25
        actual_times = [beat.time for beat in quantized.beats]
        assert actual_times == expected_times
    
    def test_merge_with_basic(self):
        """Test merge_with method basic functionality"""
        beats1 = [
            Beat(time=0.5, position=1, confidence=0.9),
            Beat(time=1.0, position=2, confidence=0.8),
        ]
        beats2 = [
            Beat(time=0.52, position=1, confidence=0.7),  # Close to 0.5
            Beat(time=1.5, position=3, confidence=0.9),   # New beat
        ]
        
        tempo_map1 = TempoMap(beats=beats1, average_bpm=120.0)
        tempo_map2 = TempoMap(beats=beats2, average_bpm=130.0)
        
        merged = tempo_map1.merge_with(tempo_map2, weight=0.7)
        
        # Should have 3 beats (2 from first, 1 merged, 1 from second)
        assert len(merged.beats) >= 2
        
        # Average BPM should be weighted average
        expected_bpm = 120.0 * 0.7 + 130.0 * 0.3
        assert merged.average_bpm == expected_bpm
    
    def test_merge_with_invalid_weight(self, sample_beats):
        """Test merge_with with invalid weight"""
        tempo_map1 = TempoMap(beats=sample_beats, average_bpm=120.0)
        tempo_map2 = TempoMap(beats=sample_beats, average_bpm=130.0)
        
        with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
            tempo_map1.merge_with(tempo_map2, weight=1.5)
        
        with pytest.raises(ValueError, match="Weight must be between 0 and 1"):
            tempo_map1.merge_with(tempo_map2, weight=-0.1)
    
    def test_merge_with_no_close_beats(self):
        """Test merge_with when no beats are close enough to merge"""
        beats1 = [Beat(time=0.5, position=1, confidence=0.9)]
        beats2 = [Beat(time=2.0, position=2, confidence=0.8)]  # Far apart
        
        tempo_map1 = TempoMap(beats=beats1, average_bpm=120.0)
        tempo_map2 = TempoMap(beats=beats2, average_bpm=130.0)
        
        merged = tempo_map1.merge_with(tempo_map2, weight=0.5)
        
        # Should have 2 beats (no merging due to distance)
        assert len(merged.beats) == 2
        
        # Check that beats are preserved with adjusted confidence
        times = [beat.time for beat in merged.beats]
        assert 0.5 in times
        assert 2.0 in times
    
    def test_merge_with_preserves_properties(self, sample_beats):
        """Test that merge_with preserves other properties"""
        tempo_map1 = TempoMap(
            beats=sample_beats,
            average_bpm=120.0,
            time_signature=(4, 4)
        )
        tempo_map2 = TempoMap(beats=sample_beats, average_bpm=130.0)
        
        merged = tempo_map1.merge_with(tempo_map2, weight=0.5)
        
        # Should preserve time signature from first tempo map
        assert merged.time_signature == (4, 4)
        
        # Tempo curve should be None (not implemented)
        assert merged.tempo_curve is None
        assert merged.tempo_confidence is None
        assert merged.downbeats is None