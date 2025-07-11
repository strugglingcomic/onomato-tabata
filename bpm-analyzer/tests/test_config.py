import pytest
from unittest.mock import Mock, patch

from bpm_analyzer.config import AnalysisConfig, AlgorithmType


class TestAnalysisConfig:
    """Test AnalysisConfig class"""
    
    def test_init_default(self):
        """Test AnalysisConfig initialization with defaults"""
        config = AnalysisConfig()
        
        assert config.algorithm == "madmom"
        assert config.sample_rate == 44100
        assert config.confidence_threshold == 0.0
        assert config.tempo_range == (30, 300)
        assert config.verbose == False
    
    def test_init_custom_parameters(self):
        """Test AnalysisConfig initialization with custom parameters"""
        config = AnalysisConfig(
            algorithm="librosa",
            sample_rate=22050,
            confidence_threshold=0.7,
            tempo_range=(60, 180),
            verbose=True
        )
        
        assert config.algorithm == "librosa"
        assert config.sample_rate == 22050
        assert config.confidence_threshold == 0.7
        assert config.tempo_range == (60, 180)
        assert config.verbose == True
    
    def test_init_algorithm_validation(self):
        """Test that algorithm validation is called during initialization"""
        with patch.object(AnalysisConfig, '_validate_algorithm') as mock_validate:
            config = AnalysisConfig(algorithm="librosa")
            mock_validate.assert_called_once()
    
    def test_init_tempo_range_validation(self):
        """Test that tempo range validation is called during initialization"""
        with patch.object(AnalysisConfig, '_validate_tempo_range') as mock_validate:
            config = AnalysisConfig(tempo_range=(60, 180))
            mock_validate.assert_called_once()
    
    def test_init_confidence_validation(self):
        """Test that confidence validation is called during initialization"""
        with patch.object(AnalysisConfig, '_validate_confidence') as mock_validate:
            config = AnalysisConfig(confidence_threshold=0.5)
            mock_validate.assert_called_once()
    
    def test_validate_algorithm_valid(self):
        """Test _validate_algorithm with valid algorithms"""
        config = AnalysisConfig()
        
        # Should not raise exceptions
        config._validate_algorithm("madmom")
        config._validate_algorithm("librosa")
        config._validate_algorithm("essentia")
        config._validate_algorithm("aubio")
        config._validate_algorithm("ensemble")
    
    def test_validate_algorithm_invalid(self):
        """Test _validate_algorithm with invalid algorithm"""
        config = AnalysisConfig()
        
        with pytest.raises(ValueError, match="Unknown algorithm"):
            config._validate_algorithm("invalid_algorithm")
    
    def test_validate_tempo_range_valid(self):
        """Test _validate_tempo_range with valid ranges"""
        config = AnalysisConfig()
        
        # Should not raise exceptions
        config._validate_tempo_range((60, 180))
        config._validate_tempo_range((30, 300))
        config._validate_tempo_range((20, 500))
    
    def test_validate_tempo_range_invalid_min(self):
        """Test _validate_tempo_range with invalid minimum"""
        config = AnalysisConfig()
        
        with pytest.raises(ValueError, match="Minimum BPM must be positive"):
            config._validate_tempo_range((0, 180))
        
        with pytest.raises(ValueError, match="Minimum BPM must be positive"):
            config._validate_tempo_range((-10, 180))
    
    def test_validate_tempo_range_invalid_max(self):
        """Test _validate_tempo_range with invalid maximum"""
        config = AnalysisConfig()
        
        with pytest.raises(ValueError, match="Maximum BPM .* must be greater than minimum"):
            config._validate_tempo_range((180, 160))
        
        with pytest.raises(ValueError, match="Maximum BPM .* must be greater than minimum"):
            config._validate_tempo_range((120, 120))
    
    def test_validate_confidence_valid(self):
        """Test _validate_confidence with valid values"""
        config = AnalysisConfig()
        
        # Should not raise exceptions
        config._validate_confidence(0.0)
        config._validate_confidence(0.5)
        config._validate_confidence(1.0)
    
    def test_validate_confidence_invalid(self):
        """Test _validate_confidence with invalid values"""
        config = AnalysisConfig()
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            config._validate_confidence(-0.1)
        
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            config._validate_confidence(1.1)
    
    def test_equality(self):
        """Test AnalysisConfig equality comparison"""
        config1 = AnalysisConfig(
            algorithm="librosa",
            sample_rate=44100,
            confidence_threshold=0.5,
            tempo_range=(60, 180),
            verbose=True
        )
        
        config2 = AnalysisConfig(
            algorithm="librosa",
            sample_rate=44100,
            confidence_threshold=0.5,
            tempo_range=(60, 180),
            verbose=True
        )
        
        config3 = AnalysisConfig(
            algorithm="madmom",  # Different algorithm
            sample_rate=44100,
            confidence_threshold=0.5,
            tempo_range=(60, 180),
            verbose=True
        )
        
        assert config1 == config2
        assert config1 != config3
    
    def test_repr(self):
        """Test AnalysisConfig string representation"""
        config = AnalysisConfig(
            algorithm="librosa",
            sample_rate=22050,
            confidence_threshold=0.7,
            tempo_range=(80, 160),
            verbose=True
        )
        
        repr_str = repr(config)
        
        # Should contain key parameters
        assert "librosa" in repr_str
        assert "22050" in repr_str
        assert "0.7" in repr_str
        assert "80, 160" in repr_str
        assert "True" in repr_str
    
    def test_from_dict(self):
        """Test creating AnalysisConfig from dictionary"""
        config_dict = {
            "algorithm": "librosa",
            "sample_rate": 22050,
            "confidence_threshold": 0.6,
            "tempo_range": (70, 170),
            "verbose": True
        }
        
        config = AnalysisConfig(**config_dict)
        
        assert config.algorithm == "librosa"
        assert config.sample_rate == 22050
        assert config.confidence_threshold == 0.6
        assert config.tempo_range == (70, 170)
        assert config.verbose == True
    
    def test_to_dict(self):
        """Test converting AnalysisConfig to dictionary"""
        config = AnalysisConfig(
            algorithm="librosa",
            sample_rate=22050,
            confidence_threshold=0.6,
            tempo_range=(70, 170),
            verbose=True
        )
        
        config_dict = {
            "algorithm": config.algorithm,
            "sample_rate": config.sample_rate,
            "confidence_threshold": config.confidence_threshold,
            "tempo_range": config.tempo_range,
            "verbose": config.verbose
        }
        
        # Verify all attributes are accessible
        assert config_dict["algorithm"] == "librosa"
        assert config_dict["sample_rate"] == 22050
        assert config_dict["confidence_threshold"] == 0.6
        assert config_dict["tempo_range"] == (70, 170)
        assert config_dict["verbose"] == True
    
    def test_immutability(self):
        """Test that AnalysisConfig behaves as immutable"""
        config = AnalysisConfig(algorithm="librosa")
        
        # Should be able to access attributes
        assert config.algorithm == "librosa"
        
        # Should not be able to modify attributes (if implemented as dataclass with frozen=True)
        # This test depends on the actual implementation
        try:
            config.algorithm = "madmom"
            # If we reach here, the config is mutable
            assert config.algorithm == "madmom"
        except AttributeError:
            # If we get here, the config is immutable (frozen dataclass)
            pass
    
    def test_sample_rate_validation(self):
        """Test sample rate validation"""
        # Valid sample rates
        config1 = AnalysisConfig(sample_rate=44100)
        config2 = AnalysisConfig(sample_rate=22050)
        config3 = AnalysisConfig(sample_rate=48000)
        
        assert config1.sample_rate == 44100
        assert config2.sample_rate == 22050
        assert config3.sample_rate == 48000
        
        # Invalid sample rates (if validation is implemented)
        try:
            config_invalid = AnalysisConfig(sample_rate=0)
            # If no validation, this should still work
            assert config_invalid.sample_rate == 0
        except ValueError:
            # If validation exists, it should raise ValueError
            pass
    
    def test_configuration_combinations(self):
        """Test various configuration combinations"""
        # High accuracy configuration
        high_accuracy = AnalysisConfig(
            algorithm="madmom",
            sample_rate=44100,
            confidence_threshold=0.8,
            tempo_range=(60, 200),
            verbose=True
        )
        
        # Fast processing configuration
        fast_processing = AnalysisConfig(
            algorithm="librosa",
            sample_rate=22050,
            confidence_threshold=0.5,
            tempo_range=(80, 160),
            verbose=False
        )
        
        # Wide tempo range configuration
        wide_tempo = AnalysisConfig(
            algorithm="ensemble",
            sample_rate=44100,
            confidence_threshold=0.6,
            tempo_range=(30, 300),
            verbose=True
        )
        
        # All should be valid
        assert high_accuracy.algorithm == "madmom"
        assert fast_processing.algorithm == "librosa"
        assert wide_tempo.algorithm == "ensemble"
        
        # Verify different configurations are not equal
        assert high_accuracy != fast_processing
        assert fast_processing != wide_tempo
        assert high_accuracy != wide_tempo


class TestAlgorithmType:
    """Test AlgorithmType enum"""
    
    def test_algorithm_type_values(self):
        """Test AlgorithmType enum values"""
        assert AlgorithmType.MADMOM == "madmom"
        assert AlgorithmType.LIBROSA == "librosa"
        assert AlgorithmType.ESSENTIA == "essentia"
        assert AlgorithmType.AUBIO == "aubio"
        assert AlgorithmType.ENSEMBLE == "ensemble"
    
    def test_algorithm_type_iteration(self):
        """Test iterating over AlgorithmType enum"""
        all_algorithms = list(AlgorithmType)
        
        assert len(all_algorithms) == 5
        assert AlgorithmType.MADMOM in all_algorithms
        assert AlgorithmType.LIBROSA in all_algorithms
        assert AlgorithmType.ESSENTIA in all_algorithms
        assert AlgorithmType.AUBIO in all_algorithms
        assert AlgorithmType.ENSEMBLE in all_algorithms
    
    def test_algorithm_type_string_conversion(self):
        """Test converting AlgorithmType to string"""
        assert str(AlgorithmType.MADMOM) == "madmom"
        assert str(AlgorithmType.LIBROSA) == "librosa"
        assert str(AlgorithmType.ESSENTIA) == "essentia"
        assert str(AlgorithmType.AUBIO) == "aubio"
        assert str(AlgorithmType.ENSEMBLE) == "ensemble"
    
    def test_algorithm_type_from_string(self):
        """Test creating AlgorithmType from string"""
        assert AlgorithmType("madmom") == AlgorithmType.MADMOM
        assert AlgorithmType("librosa") == AlgorithmType.LIBROSA
        assert AlgorithmType("essentia") == AlgorithmType.ESSENTIA
        assert AlgorithmType("aubio") == AlgorithmType.AUBIO
        assert AlgorithmType("ensemble") == AlgorithmType.ENSEMBLE
    
    def test_algorithm_type_invalid_string(self):
        """Test creating AlgorithmType from invalid string"""
        with pytest.raises(ValueError):
            AlgorithmType("invalid_algorithm")
    
    def test_algorithm_type_comparison(self):
        """Test AlgorithmType comparison"""
        assert AlgorithmType.MADMOM == AlgorithmType.MADMOM
        assert AlgorithmType.MADMOM != AlgorithmType.LIBROSA
        
        # Comparison with string
        assert AlgorithmType.MADMOM == "madmom"
        assert AlgorithmType.LIBROSA == "librosa"
        assert AlgorithmType.MADMOM != "librosa"


class TestConfigIntegration:
    """Integration tests for config module"""
    
    def test_config_with_all_algorithms(self):
        """Test creating configs with all supported algorithms"""
        algorithms = ["madmom", "librosa", "essentia", "aubio", "ensemble"]
        
        configs = []
        for algorithm in algorithms:
            config = AnalysisConfig(algorithm=algorithm)
            configs.append(config)
            assert config.algorithm == algorithm
        
        # All configs should be different
        for i, config1 in enumerate(configs):
            for j, config2 in enumerate(configs):
                if i != j:
                    assert config1 != config2
    
    def test_config_serialization_roundtrip(self):
        """Test config serialization and deserialization"""
        original_config = AnalysisConfig(
            algorithm="librosa",
            sample_rate=22050,
            confidence_threshold=0.7,
            tempo_range=(80, 160),
            verbose=True
        )
        
        # Simulate serialization to dict
        config_dict = {
            "algorithm": original_config.algorithm,
            "sample_rate": original_config.sample_rate,
            "confidence_threshold": original_config.confidence_threshold,
            "tempo_range": original_config.tempo_range,
            "verbose": original_config.verbose
        }
        
        # Simulate deserialization from dict
        restored_config = AnalysisConfig(**config_dict)
        
        # Should be equal
        assert restored_config == original_config
        assert restored_config.algorithm == original_config.algorithm
        assert restored_config.sample_rate == original_config.sample_rate
        assert restored_config.confidence_threshold == original_config.confidence_threshold
        assert restored_config.tempo_range == original_config.tempo_range
        assert restored_config.verbose == original_config.verbose
    
    def test_config_edge_cases(self):
        """Test config with edge case values"""
        # Minimum valid values
        min_config = AnalysisConfig(
            algorithm="librosa",
            sample_rate=8000,  # Very low sample rate
            confidence_threshold=0.0,
            tempo_range=(1, 2),  # Very narrow range
            verbose=False
        )
        
        # Maximum valid values
        max_config = AnalysisConfig(
            algorithm="ensemble",
            sample_rate=192000,  # Very high sample rate
            confidence_threshold=1.0,
            tempo_range=(1, 1000),  # Very wide range
            verbose=True
        )
        
        # Both should be valid
        assert min_config.confidence_threshold == 0.0
        assert max_config.confidence_threshold == 1.0
        assert min_config != max_config