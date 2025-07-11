"""
Configuration management for BPM Analyzer
"""
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

import yaml
from pydantic import BaseModel, Field, validator


class AlgorithmType(str, Enum):
    """Supported BPM detection algorithms"""
    MADMOM = "madmom"
    ESSENTIA = "essentia"
    LIBROSA = "librosa"
    AUBIO = "aubio"
    ENSEMBLE = "ensemble"


class OutputFormat(str, Enum):
    """Supported output formats"""
    JAMS = "jams"
    CSV = "csv"
    JSON = "json"


@dataclass
class AnalysisConfig:
    """Configuration for audio analysis"""
    
    # Algorithm settings
    algorithm: str = AlgorithmType.MADMOM
    ensemble_algorithms: list[str] = field(default_factory=lambda: ["madmom", "essentia"])
    
    # Tempo detection parameters
    tempo_range: Tuple[int, int] = (30, 300)
    confidence_threshold: float = 0.0
    
    # Audio processing
    sample_rate: int = 22050
    hop_length: int = 512
    n_fft: int = 2048
    
    # Output settings
    output_format: str = OutputFormat.JAMS
    include_confidence: bool = True
    include_tempo_curve: bool = True
    
    # Performance
    use_cache: bool = True
    cache_dir: Path = Path(".bpm_cache")
    
    # Logging
    verbose: bool = False
    debug: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.tempo_range[0] >= self.tempo_range[1]:
            raise ValueError("tempo_range min must be less than max")
        
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        
        if self.algorithm == AlgorithmType.ENSEMBLE and not self.ensemble_algorithms:
            raise ValueError("ensemble_algorithms must be specified for ensemble mode")


class MadmomConfig(BaseModel):
    """madmom-specific configuration"""
    
    # Beat tracking parameters
    fps: int = Field(default=100, description="Frames per second for onset detection")
    beats_per_bar: Optional[list[int]] = Field(
        default=[3, 4], 
        description="Possible beats per bar (time signatures)"
    )
    
    # DBN (Dynamic Bayesian Network) parameters
    transition_lambda: float = Field(
        default=100, 
        description="Transition probability parameter"
    )
    observation_lambda: int = Field(
        default=16,
        description="Observation probability parameter"
    )
    
    # Neural network selection
    nn_files: Optional[list[str]] = Field(
        default=None,
        description="Custom neural network files (None = use defaults)"
    )
    
    @validator('fps')
    def validate_fps(cls, v):
        if v < 10 or v > 1000:
            raise ValueError("fps must be between 10 and 1000")
        return v


class EssentiaConfig(BaseModel):
    """essentia-specific configuration"""
    
    # RhythmExtractor2013 parameters
    method: str = Field(
        default="degara",
        description="Beat tracking method: 'degara' or 'multifeature'"
    )
    
    # Onset detection
    onset_method: str = Field(
        default="complex",
        description="Onset detection method"
    )
    
    # Tempo estimation
    use_onset: bool = Field(
        default=True,
        description="Use onset information for tempo"
    )
    use_bands: bool = Field(
        default=True,
        description="Use frequency bands for tempo"
    )
    
    @validator('method')
    def validate_method(cls, v):
        if v not in ["degara", "multifeature"]:
            raise ValueError("method must be 'degara' or 'multifeature'")
        return v


class LibrosaConfig(BaseModel):
    """librosa-specific configuration"""
    
    # Beat tracking parameters
    trim: bool = Field(default=True, description="Trim silence from audio")
    onset_envelope: Optional[str] = Field(
        default=None,
        description="Pre-computed onset envelope"
    )
    
    # Tempo estimation
    aggregate: Optional[str] = Field(
        default=None,
        description="Aggregation method for tempo"
    )
    
    # Dynamic programming parameters
    tightness: float = Field(
        default=100.0,
        description="Tightness of beat distribution"
    )
    
    @validator('tightness')
    def validate_tightness(cls, v):
        if v <= 0:
            raise ValueError("tightness must be positive")
        return v


class BatchConfig(BaseModel):
    """Batch processing configuration"""
    
    # File discovery
    file_patterns: list[str] = Field(
        default=["*.mp3", "*.wav", "*.flac", "*.m4a", "*.ogg"],
        description="File patterns to match"
    )
    recursive: bool = Field(default=True, description="Search subdirectories")
    follow_symlinks: bool = Field(default=False, description="Follow symbolic links")
    
    # Processing
    parallel: bool = Field(default=True, description="Use parallel processing")
    num_workers: Optional[int] = Field(default=None, description="Number of workers")
    chunk_size: int = Field(default=10, description="Files per processing chunk")
    
    # Error handling
    skip_errors: bool = Field(default=True, description="Continue on errors")
    retry_failed: int = Field(default=1, description="Number of retries")
    
    # Output
    preserve_structure: bool = Field(
        default=True,
        description="Preserve directory structure in output"
    )
    
    @validator('num_workers')
    def validate_workers(cls, v):
        if v is not None and v < 1:
            raise ValueError("num_workers must be at least 1")
        return v


class DatabaseConfig(BaseModel):
    """Database configuration"""
    
    # Connection
    url: str = Field(
        default="sqlite:///music_tempo.db",
        description="Database connection URL"
    )
    
    # Connection pool settings
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    
    # Performance
    echo: bool = Field(default=False, description="Echo SQL statements")
    
    # Schema
    schema_name: Optional[str] = Field(
        default=None,
        description="Database schema name (PostgreSQL)"
    )


class GlobalConfig(BaseModel):
    """Global application configuration"""
    
    # General settings
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    
    # Algorithm-specific configs
    madmom: MadmomConfig = Field(default_factory=MadmomConfig)
    essentia: EssentiaConfig = Field(default_factory=EssentiaConfig)
    librosa: LibrosaConfig = Field(default_factory=LibrosaConfig)
    
    # Batch processing
    batch: BatchConfig = Field(default_factory=BatchConfig)
    
    # Database
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Paths
    cache_dir: Path = Field(default=Path.home() / ".bpm_analyzer" / "cache")
    log_dir: Path = Field(default=Path.home() / ".bpm_analyzer" / "logs")
    
    @classmethod
    def from_file(cls, config_path: Path) -> "GlobalConfig":
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)
    
    def to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(self.dict(), f, default_flow_style=False)
    
    @classmethod
    def default_config_path(cls) -> Path:
        """Get default configuration file path"""
        return Path.home() / ".bpm_analyzer" / "config.yaml"
    
    @classmethod
    def load_or_create_default(cls) -> "GlobalConfig":
        """Load config from default location or create if not exists"""
        config_path = cls.default_config_path()
        
        if config_path.exists():
            try:
                return cls.from_file(config_path)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
                print("Using default configuration")
        
        # Create default config
        config = cls()
        config.to_file(config_path)
        return config


# Convenience function for getting config
_global_config: Optional[GlobalConfig] = None


def get_config() -> GlobalConfig:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = GlobalConfig.load_or_create_default()
    return _global_config


def set_config(config: GlobalConfig) -> None:
    """Set the global configuration instance"""
    global _global_config
    _global_config = config


# Example configuration file content
EXAMPLE_CONFIG_YAML = """
# BPM Analyzer Configuration

analysis:
  algorithm: madmom
  ensemble_algorithms: [madmom, essentia]
  tempo_range: [60, 180]
  confidence_threshold: 0.7
  sample_rate: 22050
  verbose: false

madmom:
  fps: 100
  beats_per_bar: [3, 4]
  transition_lambda: 100
  observation_lambda: 16

essentia:
  method: degara
  onset_method: complex
  use_onset: true
  use_bands: true

librosa:
  trim: true
  tightness: 100.0

batch:
  file_patterns: ["*.mp3", "*.wav", "*.flac"]
  recursive: true
  parallel: true
  skip_errors: true
  preserve_structure: true

database:
  url: sqlite:///music_tempo.db
  pool_size: 5
  echo: false

cache_dir: ~/.bpm_analyzer/cache
log_dir: ~/.bpm_analyzer/logs
"""
