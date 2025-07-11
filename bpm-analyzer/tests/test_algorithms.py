import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from bpm_analyzer.algorithms.base import BeatDetector, AlgorithmResult
from bpm_analyzer.algorithms.librosa_impl import LibrosaDetector
from bpm_analyzer.core.tempo_map import TempoMap, Beat
from bpm_analyzer.io.audio_loader import AudioData
from bpm_analyzer.config import AnalysisConfig


class TestBeatDetectorBase:
    """Test BeatDetector base class"""
    
    def test_init_with_config(self, sample_analysis_config):
        """Test BeatDetector initialization with config"""
        
        class TestDetector(BeatDetector):
            @property
            def name(self) -> str:
                return "test"
            
            def detect(self, audio_data: AudioData) -> TempoMap:
                return TempoMap(beats=[Beat(time=1.0, position=1)], average_bpm=120.0)
        
        detector = TestDetector(sample_analysis_config)
        assert detector.config == sample_analysis_config
    
    def test_abstract_methods(self):
        """Test that abstract methods must be implemented"""
        
        class IncompleteDetector(BeatDetector):
            pass
        
        with pytest.raises(TypeError):
            IncompleteDetector(AnalysisConfig())
    
    def test_supports_properties(self, sample_analysis_config):
        """Test support properties default values"""
        
        class TestDetector(BeatDetector):
            @property
            def name(self) -> str:
                return "test"
            
            def detect(self, audio_data: AudioData) -> TempoMap:
                return TempoMap(beats=[Beat(time=1.0, position=1)], average_bpm=120.0)
        
        detector = TestDetector(sample_analysis_config)
        assert detector.supports_variable_tempo == False
        assert detector.supports_downbeats == False
    
    def test_preprocess_audio_default(self, sample_analysis_config, sample_audio_data):
        """Test default preprocess_audio method"""
        
        class TestDetector(BeatDetector):
            @property
            def name(self) -> str:
                return "test"
            
            def detect(self, audio_data: AudioData) -> TempoMap:
                return TempoMap(beats=[Beat(time=1.0, position=1)], average_bpm=120.0)
        
        detector = TestDetector(sample_analysis_config)
        result = detector.preprocess_audio(sample_audio_data)
        
        # Should return same object by default
        assert result is sample_audio_data
    
    def test_postprocess_tempo_map_default(self, sample_analysis_config, sample_tempo_map):
        """Test default postprocess_tempo_map method"""
        
        class TestDetector(BeatDetector):
            @property
            def name(self) -> str:
                return "test"
            
            def detect(self, audio_data: AudioData) -> TempoMap:
                return TempoMap(beats=[Beat(time=1.0, position=1)], average_bpm=120.0)
        
        detector = TestDetector(sample_analysis_config)
        result = detector.postprocess_tempo_map(sample_tempo_map)
        
        # Should return same object by default
        assert result is sample_tempo_map


class TestLibrosaDetector:
    """Test LibrosaDetector implementation"""
    
    def test_init(self, sample_analysis_config):
        """Test LibrosaDetector initialization"""
        detector = LibrosaDetector(sample_analysis_config)
        assert detector.config == sample_analysis_config
        assert detector.name == "librosa"
    
    def test_name_property(self, sample_analysis_config):
        """Test name property"""
        detector = LibrosaDetector(sample_analysis_config)
        assert detector.name == "librosa"
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_success(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test successful beat detection"""
        # Mock librosa functions
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([10, 20, 30, 40]))
        mock_librosa.frames_to_time.return_value = np.array([0.5, 1.0, 1.5, 2.0])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        # Verify result
        assert isinstance(result, TempoMap)
        assert result.average_bpm == 120.0
        assert len(result.beats) == 4
        assert result.beats[0].time == 0.5
        assert result.beats[0].position == 1
        assert result.beats[1].position == 2
        assert result.beats[2].position == 3
        assert result.beats[3].position == 4
        
        # Verify librosa was called correctly
        mock_librosa.beat.beat_track.assert_called_once_with(
            y=sample_audio_data.audio,
            sr=sample_audio_data.sample_rate,
            hop_length=512
        )
        mock_librosa.frames_to_time.assert_called_once_with(
            np.array([10, 20, 30, 40]),
            sr=sample_audio_data.sample_rate,
            hop_length=512
        )
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_single_beat(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test detection with single beat"""
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([10]))
        mock_librosa.frames_to_time.return_value = np.array([0.5])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        assert len(result.beats) == 1
        assert result.beats[0].time == 0.5
        assert result.beats[0].position == 1
        assert result.beats[0].confidence == 0.8
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_many_beats(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test detection with many beats"""
        # Test beat positions cycling through 1,2,3,4
        beat_frames = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90])
        beat_times = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5])
        
        mock_librosa.beat.beat_track.return_value = (120.0, beat_frames)
        mock_librosa.frames_to_time.return_value = beat_times
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        assert len(result.beats) == 9
        
        # Check position cycling
        expected_positions = [1, 2, 3, 4, 1, 2, 3, 4, 1]
        for i, beat in enumerate(result.beats):
            assert beat.position == expected_positions[i]
    
    def test_detect_librosa_not_installed(self, sample_analysis_config, sample_audio_data):
        """Test detection when librosa is not installed"""
        with patch('bpm_analyzer.algorithms.librosa_impl.librosa', side_effect=ImportError):
            detector = LibrosaDetector(sample_analysis_config)
            
            with pytest.raises(ImportError, match="librosa is not installed"):
                detector.detect(sample_audio_data)
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_librosa_error(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test detection when librosa raises an error"""
        mock_librosa.beat.beat_track.side_effect = Exception("Librosa processing error")
        
        detector = LibrosaDetector(sample_analysis_config)
        
        with pytest.raises(Exception, match="Librosa processing error"):
            detector.detect(sample_audio_data)
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_empty_beats(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test detection with no beats found"""
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([]))
        mock_librosa.frames_to_time.return_value = np.array([])
        
        detector = LibrosaDetector(sample_analysis_config)
        
        with pytest.raises(ValueError, match="TempoMap must contain at least one beat"):
            detector.detect(sample_audio_data)
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_zero_tempo(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test detection with zero tempo"""
        mock_librosa.beat.beat_track.return_value = (0.0, np.array([10]))
        mock_librosa.frames_to_time.return_value = np.array([0.5])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        assert result.average_bpm == 0.0
        assert len(result.beats) == 1
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_confidence_values(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test that all beats have the same confidence value"""
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([10, 20, 30]))
        mock_librosa.frames_to_time.return_value = np.array([0.5, 1.0, 1.5])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        # All beats should have the same confidence (librosa doesn't provide per-beat confidence)
        for beat in result.beats:
            assert beat.confidence == 0.8
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_beat_times_order(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test that beat times are in correct order"""
        # Provide unordered beat times to test sorting
        beat_times = np.array([1.5, 0.5, 2.0, 1.0])
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([20, 10, 30, 15]))
        mock_librosa.frames_to_time.return_value = beat_times
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        # Beats should be sorted by time
        beat_times_result = [beat.time for beat in result.beats]
        assert beat_times_result == sorted(beat_times_result)
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_downbeats_none(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test that downbeats are None (not supported by librosa implementation)"""
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([10, 20]))
        mock_librosa.frames_to_time.return_value = np.array([0.5, 1.0])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        assert result.downbeats is None
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_detect_tempo_curve_none(self, mock_librosa, sample_analysis_config, sample_audio_data):
        """Test that tempo curve is None (not supported by librosa implementation)"""
        mock_librosa.beat.beat_track.return_value = (120.0, np.array([10, 20]))
        mock_librosa.frames_to_time.return_value = np.array([0.5, 1.0])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(sample_audio_data)
        
        assert result.tempo_curve is None
        assert result.tempo_confidence is None


class TestAlgorithmResult:
    """Test AlgorithmResult dataclass"""
    
    def test_init(self, sample_tempo_map):
        """Test AlgorithmResult initialization"""
        metadata = {"parameter1": "value1", "parameter2": 42}
        warnings = ["warning1", "warning2"]
        
        result = AlgorithmResult(
            tempo_map=sample_tempo_map,
            metadata=metadata,
            warnings=warnings
        )
        
        assert result.tempo_map == sample_tempo_map
        assert result.metadata == metadata
        assert result.warnings == warnings
    
    def test_init_empty_metadata_warnings(self, sample_tempo_map):
        """Test AlgorithmResult with empty metadata and warnings"""
        result = AlgorithmResult(
            tempo_map=sample_tempo_map,
            metadata={},
            warnings=[]
        )
        
        assert result.tempo_map == sample_tempo_map
        assert result.metadata == {}
        assert result.warnings == []


class TestAlgorithmIntegration:
    """Integration tests for algorithm implementations"""
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_librosa_detector_realistic_scenario(self, mock_librosa, sample_analysis_config):
        """Test LibrosaDetector with realistic scenario"""
        # Simulate a 3-minute song at 128 BPM
        duration = 180.0  # 3 minutes
        bpm = 128.0
        sample_rate = 44100
        
        # Calculate expected number of beats
        expected_beats = int(duration * bpm / 60)
        
        # Create mock beat data
        beat_frames = np.arange(0, expected_beats) * (sample_rate * 60 / bpm / 512)
        beat_times = np.arange(0, expected_beats) * (60 / bpm)
        
        mock_librosa.beat.beat_track.return_value = (bpm, beat_frames)
        mock_librosa.frames_to_time.return_value = beat_times
        
        # Create audio data
        audio_data = AudioData(
            audio=np.random.randn(int(duration * sample_rate)).astype(np.float32),
            sample_rate=sample_rate,
            duration=duration,
            channels=1
        )
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(audio_data)
        
        # Verify realistic results
        assert result.average_bpm == bpm
        assert len(result.beats) == expected_beats
        assert result.beats[0].time == 0.0
        assert result.beats[-1].time <= duration
        
        # Check that beat positions cycle through 1,2,3,4
        positions = [beat.position for beat in result.beats]
        expected_positions = [((i % 4) + 1) for i in range(expected_beats)]
        assert positions == expected_positions
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_librosa_detector_edge_cases(self, mock_librosa, sample_analysis_config):
        """Test LibrosaDetector with edge cases"""
        # Test very short audio
        short_audio = AudioData(
            audio=np.random.randn(1024).astype(np.float32),
            sample_rate=44100,
            duration=1024/44100,  # ~0.023 seconds
            channels=1
        )
        
        mock_librosa.beat.beat_track.return_value = (60.0, np.array([5]))
        mock_librosa.frames_to_time.return_value = np.array([0.01])
        
        detector = LibrosaDetector(sample_analysis_config)
        result = detector.detect(short_audio)
        
        assert len(result.beats) == 1
        assert result.beats[0].time == 0.01
        
        # Test very high BPM
        mock_librosa.beat.beat_track.return_value = (300.0, np.array([10, 15, 20]))
        mock_librosa.frames_to_time.return_value = np.array([0.1, 0.3, 0.5])
        
        result = detector.detect(short_audio)
        assert result.average_bpm == 300.0
        assert len(result.beats) == 3
    
    def test_multiple_algorithm_consistency(self, sample_analysis_config, sample_audio_data):
        """Test that multiple detector instances produce consistent results"""
        with patch('bpm_analyzer.algorithms.librosa_impl.librosa') as mock_librosa:
            mock_librosa.beat.beat_track.return_value = (120.0, np.array([10, 20, 30]))
            mock_librosa.frames_to_time.return_value = np.array([0.5, 1.0, 1.5])
            
            detector1 = LibrosaDetector(sample_analysis_config)
            detector2 = LibrosaDetector(sample_analysis_config)
            
            result1 = detector1.detect(sample_audio_data)
            result2 = detector2.detect(sample_audio_data)
            
            # Results should be identical
            assert result1.average_bpm == result2.average_bpm
            assert len(result1.beats) == len(result2.beats)
            
            for beat1, beat2 in zip(result1.beats, result2.beats):
                assert beat1.time == beat2.time
                assert beat1.position == beat2.position
                assert beat1.confidence == beat2.confidence