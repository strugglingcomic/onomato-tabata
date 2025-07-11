import pytest
import logging
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

from bpm_analyzer.utils.validation import (
    ValidationResult,
    validate_audio_file,
    validate_tempo_range,
    validate_confidence
)
from bpm_analyzer.utils.logging import get_logger, setup_logging
from bpm_analyzer.utils.audio_utils import (
    resample_audio,
    normalize_audio,
    convert_to_mono
)
from bpm_analyzer.core.exceptions import ValidationError


class TestValidation:
    """Test validation utilities"""
    
    def test_validation_result_init(self):
        """Test ValidationResult initialization"""
        result = ValidationResult(
            is_valid=True,
            format="wav",
            duration=10.0,
            sample_rate=44100,
            channels=2
        )
        
        assert result.is_valid == True
        assert result.error is None
        assert result.format == "wav"
        assert result.duration == 10.0
        assert result.sample_rate == 44100
        assert result.channels == 2
    
    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid file"""
        result = ValidationResult(
            is_valid=False,
            error="File not found"
        )
        
        assert result.is_valid == False
        assert result.error == "File not found"
        assert result.format is None
        assert result.duration is None
    
    def test_validate_audio_file_not_exists(self):
        """Test validation of non-existent file"""
        result = validate_audio_file(Path("/nonexistent/file.mp3"))
        
        assert result.is_valid == False
        assert "File not found" in result.error
    
    def test_validate_audio_file_not_file(self, temp_output_dir):
        """Test validation of directory instead of file"""
        result = validate_audio_file(temp_output_dir)
        
        assert result.is_valid == False
        assert "Not a file" in result.error
    
    def test_validate_audio_file_empty(self, temp_output_dir):
        """Test validation of empty file"""
        empty_file = temp_output_dir / "empty.mp3"
        empty_file.touch()
        
        result = validate_audio_file(empty_file)
        
        assert result.is_valid == False
        assert "File is empty" in result.error
    
    def test_validate_audio_file_too_large(self, temp_output_dir):
        """Test validation of file that's too large"""
        large_file = temp_output_dir / "large.mp3"
        
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 2e9  # 2GB
            mock_stat.return_value.st_size = 2e9
            
            # Need to make the file exist
            large_file.touch()
            
            result = validate_audio_file(large_file)
            
            assert result.is_valid == False
            assert "File too large" in result.error
    
    @patch('bpm_analyzer.utils.validation.sf.info')
    def test_validate_audio_file_success_soundfile(self, mock_sf_info, temp_audio_file):
        """Test successful validation using soundfile"""
        mock_info = Mock()
        mock_info.format = "WAV"
        mock_info.duration = 5.0
        mock_info.samplerate = 44100
        mock_info.channels = 1
        mock_sf_info.return_value = mock_info
        
        result = validate_audio_file(temp_audio_file)
        
        assert result.is_valid == True
        assert result.format == "WAV"
        assert result.duration == 5.0
        assert result.sample_rate == 44100
        assert result.channels == 1
        
        mock_sf_info.assert_called_once_with(str(temp_audio_file))
    
    @patch('bpm_analyzer.utils.validation.sf.info')
    @patch('bpm_analyzer.utils.validation.AudioSegment')
    def test_validate_audio_file_fallback_pydub(self, mock_audio_segment, mock_sf_info, temp_audio_file):
        """Test validation fallback to pydub"""
        # Make soundfile fail
        mock_sf_info.side_effect = Exception("soundfile error")
        
        # Mock pydub success
        mock_audio = Mock()
        mock_audio.__len__.return_value = 5000  # 5 seconds in ms
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio_segment.from_file.return_value = mock_audio
        
        result = validate_audio_file(temp_audio_file)
        
        assert result.is_valid == True
        assert result.format == temp_audio_file.suffix[1:]
        assert result.duration == 5.0
        assert result.sample_rate == 44100
        assert result.channels == 2
        
        mock_audio_segment.from_file.assert_called_once_with(str(temp_audio_file))
    
    @patch('bpm_analyzer.utils.validation.sf.info')
    @patch('bpm_analyzer.utils.validation.AudioSegment')
    def test_validate_audio_file_both_fail(self, mock_audio_segment, mock_sf_info, temp_audio_file):
        """Test validation when both soundfile and pydub fail"""
        mock_sf_info.side_effect = Exception("soundfile error")
        mock_audio_segment.from_file.side_effect = Exception("pydub error")
        
        result = validate_audio_file(temp_audio_file)
        
        assert result.is_valid == False
        assert "Cannot read audio file" in result.error
    
    def test_validate_tempo_range_valid(self):
        """Test valid tempo range validation"""
        # Should not raise exception
        validate_tempo_range((60, 180))
        validate_tempo_range((20, 500))
        validate_tempo_range((100, 150))
    
    def test_validate_tempo_range_min_negative(self):
        """Test tempo range with negative minimum"""
        with pytest.raises(ValidationError, match="Minimum BPM must be positive"):
            validate_tempo_range((-10, 120))
    
    def test_validate_tempo_range_min_zero(self):
        """Test tempo range with zero minimum"""
        with pytest.raises(ValidationError, match="Minimum BPM must be positive"):
            validate_tempo_range((0, 120))
    
    def test_validate_tempo_range_max_less_than_min(self):
        """Test tempo range with max < min"""
        with pytest.raises(ValidationError, match="Maximum BPM .* must be greater than minimum"):
            validate_tempo_range((120, 100))
    
    def test_validate_tempo_range_max_equal_min(self):
        """Test tempo range with max = min"""
        with pytest.raises(ValidationError, match="Maximum BPM .* must be greater than minimum"):
            validate_tempo_range((120, 120))
    
    def test_validate_tempo_range_min_too_low(self):
        """Test tempo range with minimum too low"""
        with pytest.raises(ValidationError, match="Minimum BPM too low"):
            validate_tempo_range((10, 120))
    
    def test_validate_tempo_range_max_too_high(self):
        """Test tempo range with maximum too high"""
        with pytest.raises(ValidationError, match="Maximum BPM too high"):
            validate_tempo_range((120, 600))
    
    def test_validate_confidence_valid(self):
        """Test valid confidence validation"""
        # Should not raise exception
        validate_confidence(0.0)
        validate_confidence(0.5)
        validate_confidence(1.0)
    
    def test_validate_confidence_negative(self):
        """Test negative confidence"""
        with pytest.raises(ValidationError, match="Confidence must be between 0 and 1"):
            validate_confidence(-0.1)
    
    def test_validate_confidence_too_high(self):
        """Test confidence > 1"""
        with pytest.raises(ValidationError, match="Confidence must be between 0 and 1"):
            validate_confidence(1.1)


class TestLogging:
    """Test logging utilities"""
    
    def test_get_logger(self):
        """Test getting logger instance"""
        logger = get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_get_logger_different_names(self):
        """Test getting loggers with different names"""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")
        
        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger1 is not logger2
    
    def test_get_logger_same_name(self):
        """Test getting logger with same name returns same instance"""
        logger1 = get_logger("same_logger")
        logger2 = get_logger("same_logger")
        
        assert logger1 is logger2
    
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters"""
        # Clear existing handlers
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        setup_logging()
        
        # Check that handlers were added
        assert len(root.handlers) > 0
        assert root.level == logging.INFO
        
        # Check that madmom, numba, librosa are at WARNING level
        assert logging.getLogger("madmom").level == logging.WARNING
        assert logging.getLogger("numba").level == logging.WARNING
        assert logging.getLogger("librosa").level == logging.WARNING
    
    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom level"""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        setup_logging(level="DEBUG")
        
        assert root.level == logging.DEBUG
    
    def test_setup_logging_with_file(self, temp_output_dir):
        """Test setup_logging with file handler"""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        log_file = temp_output_dir / "test.log"
        setup_logging(log_file=log_file)
        
        # Check that file handler was added
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert log_file.parent.exists()
    
    def test_setup_logging_no_rich(self):
        """Test setup_logging without rich handler"""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        
        setup_logging(use_rich=False)
        
        # Check that StreamHandler was added instead of RichHandler
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0
    
    def test_setup_logging_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers"""
        root = logging.getLogger()
        
        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        root.addHandler(dummy_handler)
        initial_count = len(root.handlers)
        
        setup_logging()
        
        # Should have different handlers now
        assert dummy_handler not in root.handlers


class TestAudioUtils:
    """Test audio processing utilities"""
    
    @patch('bpm_analyzer.utils.audio_utils.librosa')
    def test_resample_audio_same_rate(self, mock_librosa):
        """Test resampling when target rate equals source rate"""
        audio = np.array([1, 2, 3, 4, 5])
        sr = 44100
        
        result_audio, result_sr = resample_audio(audio, sr, sr)
        
        # Should return original audio unchanged
        np.testing.assert_array_equal(result_audio, audio)
        assert result_sr == sr
        
        # librosa.resample should not be called
        mock_librosa.resample.assert_not_called()
    
    @patch('bpm_analyzer.utils.audio_utils.librosa')
    def test_resample_audio_different_rate(self, mock_librosa):
        """Test resampling when target rate differs from source rate"""
        audio = np.array([1, 2, 3, 4, 5])
        sr = 44100
        target_sr = 22050
        resampled_audio = np.array([1, 3, 5])
        
        mock_librosa.resample.return_value = resampled_audio
        
        result_audio, result_sr = resample_audio(audio, sr, target_sr)
        
        np.testing.assert_array_equal(result_audio, resampled_audio)
        assert result_sr == target_sr
        
        mock_librosa.resample.assert_called_once_with(
            audio, orig_sr=sr, target_sr=target_sr
        )
    
    @patch('bpm_analyzer.utils.audio_utils.librosa')
    def test_normalize_audio(self, mock_librosa):
        """Test audio normalization"""
        audio = np.array([0.5, -0.8, 0.2, -0.1])
        normalized = np.array([0.625, -1.0, 0.25, -0.125])
        
        mock_librosa.util.normalize.return_value = normalized
        
        result = normalize_audio(audio)
        
        np.testing.assert_array_equal(result, normalized)
        mock_librosa.util.normalize.assert_called_once_with(audio)
    
    @patch('bpm_analyzer.utils.audio_utils.librosa')
    def test_convert_to_mono_already_mono(self, mock_librosa):
        """Test converting mono audio to mono"""
        audio = np.array([1, 2, 3, 4, 5])  # 1D array = mono
        
        result = convert_to_mono(audio)
        
        np.testing.assert_array_equal(result, audio)
        mock_librosa.to_mono.assert_not_called()
    
    @patch('bpm_analyzer.utils.audio_utils.librosa')
    def test_convert_to_mono_stereo(self, mock_librosa):
        """Test converting stereo audio to mono"""
        audio = np.array([[1, 2], [3, 4], [5, 6]])  # 2D array = stereo
        mono_audio = np.array([1.5, 3.5, 5.5])
        
        mock_librosa.to_mono.return_value = mono_audio
        
        result = convert_to_mono(audio)
        
        np.testing.assert_array_equal(result, mono_audio)
        mock_librosa.to_mono.assert_called_once_with(audio)
    
    def test_audio_utils_integration(self):
        """Test audio utils integration with actual librosa functions"""
        # Create test audio
        audio = np.array([0.5, -0.8, 0.2, -0.1], dtype=np.float32)
        sr = 44100
        
        # Test that functions work with real librosa
        try:
            # Test normalization
            normalized = normalize_audio(audio)
            assert isinstance(normalized, np.ndarray)
            assert len(normalized) == len(audio)
            
            # Test resampling (same rate)
            resampled, new_sr = resample_audio(audio, sr, sr)
            np.testing.assert_array_equal(resampled, audio)
            assert new_sr == sr
            
            # Test mono conversion
            mono = convert_to_mono(audio)
            np.testing.assert_array_equal(mono, audio)
            
        except ImportError:
            # Skip if librosa not available
            pytest.skip("librosa not available for integration test")


class TestUtilsIntegration:
    """Integration tests for utility functions"""
    
    def test_validation_with_real_file(self, temp_audio_file):
        """Test validation with real audio file"""
        result = validate_audio_file(temp_audio_file)
        
        # Should be valid since temp_audio_file fixture creates a real audio file
        assert result.is_valid == True
        assert result.format is not None
        assert result.duration is not None
        assert result.sample_rate is not None
        assert result.channels is not None
    
    def test_logging_with_real_file(self, temp_output_dir):
        """Test logging with real log file"""
        log_file = temp_output_dir / "integration.log"
        
        # Setup logging
        setup_logging(level="DEBUG", log_file=log_file)
        
        # Get logger and log message
        logger = get_logger("integration_test")
        logger.info("Test message")
        
        # Check that log file was created and contains message
        assert log_file.exists()
        
        # Force flush handlers
        for handler in logging.getLogger().handlers:
            handler.flush()
        
        # Read log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        assert "Test message" in content
        assert "integration_test" in content
    
    def test_tempo_range_validation_edge_cases(self):
        """Test tempo range validation with edge cases"""
        # Test boundary values
        validate_tempo_range((20, 500))  # Should not raise
        
        with pytest.raises(ValidationError):
            validate_tempo_range((19.9, 100))  # Just below minimum
        
        with pytest.raises(ValidationError):
            validate_tempo_range((100, 500.1))  # Just above maximum
    
    def test_confidence_validation_edge_cases(self):
        """Test confidence validation with edge cases"""
        # Test boundary values
        validate_confidence(0.0)  # Should not raise
        validate_confidence(1.0)  # Should not raise
        
        with pytest.raises(ValidationError):
            validate_confidence(-0.001)  # Just below minimum
        
        with pytest.raises(ValidationError):
            validate_confidence(1.001)  # Just above maximum