import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

from bpm_analyzer.core.analyzer import (
    AnalysisResult,
    AudioAnalyzer,
    analyze_file
)
from bpm_analyzer.core.tempo_map import Beat, TempoMap
from bpm_analyzer.config import AnalysisConfig
from bpm_analyzer.io.audio_loader import AudioData


class TestAnalysisResult:
    """Test AnalysisResult class"""
    
    def test_init(self, temp_audio_file, sample_beats):
        """Test AnalysisResult initialization"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa",
            processing_time=1.5
        )
        
        assert result.file_path == temp_audio_file
        assert result.duration == 5.0
        assert result.sample_rate == 44100
        assert result.average_bpm == 120.0
        assert result.beats == sample_beats
        assert result.algorithm == "librosa"
        assert result.processing_time == 1.5
        assert result.warnings == []
    
    def test_beat_times_property(self, temp_audio_file, sample_beats):
        """Test beat_times property"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats
        )
        
        expected_times = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
        np.testing.assert_array_equal(result.beat_times, expected_times)
    
    def test_beat_count_property(self, temp_audio_file, sample_beats):
        """Test beat_count property"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats
        )
        
        assert result.beat_count == 6
    
    def test_to_jams(self, temp_audio_file, sample_beats):
        """Test JAMS conversion"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa"
        )
        
        jam = result.to_jams()
        
        assert jam.file_metadata.duration == 5.0
        assert str(temp_audio_file) in jam.file_metadata.identifiers["file"]
        assert len(jam.annotations) == 2  # tempo and beat annotations
        
        # Check tempo annotation
        tempo_ann = jam.annotations[0]
        assert tempo_ann.namespace == "tempo"
        assert len(tempo_ann.data) == 1
        assert tempo_ann.data[0].value == 120.0
        
        # Check beat annotation
        beat_ann = jam.annotations[1]
        assert beat_ann.namespace == "beat"
        assert len(beat_ann.data) == 6
        assert beat_ann.data[0].time == 0.5
        assert beat_ann.data[0].value == 1
    
    def test_to_jams_with_tempo_curve(self, temp_audio_file, sample_beats):
        """Test JAMS conversion with tempo curve"""
        tempo_curve = np.array([120.0, 121.0, 119.0, 120.0])
        tempo_confidence = np.array([0.9, 0.8, 0.85, 0.9])
        
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa",
            tempo_curve=tempo_curve,
            tempo_confidence=tempo_confidence
        )
        
        jam = result.to_jams()
        tempo_ann = jam.annotations[0]
        
        # Should have tempo points for each curve value
        assert len(tempo_ann.data) == 4
        assert tempo_ann.data[0].value == 120.0
        assert tempo_ann.data[1].value == 121.0
    
    def test_to_jams_with_downbeats(self, temp_audio_file, sample_beats):
        """Test JAMS conversion with downbeats"""
        downbeats = [0.5, 2.5]
        
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa",
            downbeats=downbeats
        )
        
        jam = result.to_jams()
        
        # Should have 3 annotations: tempo, beat, and downbeat
        assert len(jam.annotations) == 3
        
        downbeat_ann = jam.annotations[2]
        assert downbeat_ann.namespace == "beat"
        assert len(downbeat_ann.data) == 2
        assert downbeat_ann.data[0].time == 0.5
        assert downbeat_ann.data[0].value == 1
    
    def test_save_jams(self, temp_audio_file, sample_beats, temp_output_dir):
        """Test saving as JAMS format"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa"
        )
        
        output_file = temp_output_dir / "test.jams"
        result.save(output_file, format="jams")
        
        assert output_file.exists()
        
        # Load and verify
        import jams
        jam = jams.load(str(output_file))
        assert jam.file_metadata.duration == 5.0
        assert len(jam.annotations) == 2
    
    def test_save_csv(self, temp_audio_file, sample_beats, temp_output_dir):
        """Test saving as CSV format"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa"
        )
        
        output_file = temp_output_dir / "test.csv"
        result.save(output_file, format="csv")
        
        assert output_file.exists()
        
        # Load and verify
        import csv
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['time', 'position', 'confidence', 'bpm']
            
            rows = list(reader)
            assert len(rows) == 6
            assert float(rows[0][0]) == 0.5
            assert int(rows[0][1]) == 1
    
    def test_save_json(self, temp_audio_file, sample_beats, temp_output_dir):
        """Test saving as JSON format"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats,
            algorithm="librosa"
        )
        
        output_file = temp_output_dir / "test.json"
        result.save(output_file, format="json")
        
        assert output_file.exists()
        
        # Load and verify
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data['duration'] == 5.0
        assert data['average_bpm'] == 120.0
        assert data['algorithm'] == "librosa"
        assert len(data['beats']) == 6
        assert data['beats'][0]['time'] == 0.5
    
    def test_save_invalid_format(self, temp_audio_file, sample_beats, temp_output_dir):
        """Test saving with invalid format"""
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=sample_beats
        )
        
        output_file = temp_output_dir / "test.invalid"
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            result.save(output_file, format="invalid")


class TestAudioAnalyzer:
    """Test AudioAnalyzer class"""
    
    def test_init_default_config(self):
        """Test AudioAnalyzer initialization with default config"""
        analyzer = AudioAnalyzer()
        
        assert analyzer.config is not None
        assert analyzer.config.algorithm == "madmom"  # default
        assert analyzer._detectors == {}
    
    def test_init_custom_config(self, sample_analysis_config):
        """Test AudioAnalyzer initialization with custom config"""
        analyzer = AudioAnalyzer(sample_analysis_config)
        
        assert analyzer.config == sample_analysis_config
        assert analyzer.config.algorithm == "librosa"
    
    def test_get_detector_librosa(self, sample_analysis_config):
        """Test getting librosa detector"""
        analyzer = AudioAnalyzer(sample_analysis_config)
        
        detector = analyzer._get_detector("librosa")
        
        assert detector is not None
        assert detector.name == "librosa"
        assert "librosa" in analyzer._detectors
    
    def test_get_detector_invalid(self, sample_analysis_config):
        """Test getting invalid detector"""
        analyzer = AudioAnalyzer(sample_analysis_config)
        
        with pytest.raises(ValueError, match="Unknown algorithm"):
            analyzer._get_detector("invalid")
    
    def test_get_detector_caching(self, sample_analysis_config):
        """Test detector caching"""
        analyzer = AudioAnalyzer(sample_analysis_config)
        
        detector1 = analyzer._get_detector("librosa")
        detector2 = analyzer._get_detector("librosa")
        
        # Should be the same instance
        assert detector1 is detector2
    
    @patch('bpm_analyzer.core.analyzer.load_audio')
    def test_analyze_success(self, mock_load_audio, sample_analysis_config, 
                           temp_audio_file, sample_audio_data, sample_tempo_map):
        """Test successful audio analysis"""
        mock_load_audio.return_value = sample_audio_data
        
        analyzer = AudioAnalyzer(sample_analysis_config)
        
        # Mock the detector
        mock_detector = Mock()
        mock_detector.detect.return_value = sample_tempo_map
        analyzer._detectors["librosa"] = mock_detector
        
        result = analyzer.analyze(temp_audio_file)
        
        assert isinstance(result, AnalysisResult)
        assert result.file_path == temp_audio_file
        assert result.duration == sample_audio_data.duration
        assert result.sample_rate == sample_audio_data.sample_rate
        assert result.average_bpm == sample_tempo_map.average_bpm
        assert result.beats == sample_tempo_map.beats
        assert result.algorithm == "librosa"
        assert result.processing_time > 0
        
        mock_load_audio.assert_called_once_with(
            temp_audio_file,
            sr=sample_analysis_config.sample_rate,
            mono=True
        )
        mock_detector.detect.assert_called_once_with(sample_audio_data)
    
    @patch('bpm_analyzer.core.analyzer.load_audio')
    def test_analyze_with_confidence_filtering(self, mock_load_audio, 
                                             temp_audio_file, sample_audio_data):
        """Test analysis with confidence filtering"""
        mock_load_audio.return_value = sample_audio_data
        
        config = AnalysisConfig(
            algorithm="librosa",
            confidence_threshold=0.8
        )
        analyzer = AudioAnalyzer(config)
        
        # Mock the detector and tempo map
        mock_detector = Mock()
        mock_tempo_map = Mock()
        mock_tempo_map.filter_by_confidence.return_value = mock_tempo_map
        mock_tempo_map.average_bpm = 120.0
        mock_tempo_map.beats = []
        mock_tempo_map.downbeats = None
        mock_tempo_map.tempo_curve = None
        mock_tempo_map.tempo_confidence = None
        
        mock_detector.detect.return_value = mock_tempo_map
        analyzer._detectors["librosa"] = mock_detector
        
        result = analyzer.analyze(temp_audio_file)
        
        mock_tempo_map.filter_by_confidence.assert_called_once_with(0.8)
        assert isinstance(result, AnalysisResult)
    
    @patch('bpm_analyzer.core.analyzer.load_audio')
    def test_analyze_audio_load_error(self, mock_load_audio, 
                                    sample_analysis_config, temp_audio_file):
        """Test analysis with audio loading error"""
        mock_load_audio.side_effect = Exception("Audio load failed")
        
        analyzer = AudioAnalyzer(sample_analysis_config)
        
        with pytest.raises(Exception, match="Audio load failed"):
            analyzer.analyze(temp_audio_file)


class TestAnalyzeFile:
    """Test analyze_file convenience function"""
    
    @patch('bpm_analyzer.core.analyzer.AudioAnalyzer')
    def test_analyze_file_default_config(self, mock_analyzer_class, temp_audio_file):
        """Test analyze_file with default config"""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_file(temp_audio_file)
        
        mock_analyzer_class.assert_called_once_with(None)
        mock_analyzer.analyze.assert_called_once_with(temp_audio_file)
        assert result == mock_result
    
    @patch('bpm_analyzer.core.analyzer.AudioAnalyzer')
    def test_analyze_file_custom_config(self, mock_analyzer_class, 
                                      temp_audio_file, sample_analysis_config):
        """Test analyze_file with custom config"""
        mock_analyzer = Mock()
        mock_result = Mock()
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer
        
        result = analyze_file(temp_audio_file, sample_analysis_config)
        
        mock_analyzer_class.assert_called_once_with(sample_analysis_config)
        mock_analyzer.analyze.assert_called_once_with(temp_audio_file)
        assert result == mock_result