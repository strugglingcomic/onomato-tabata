# BPM Analyzer

A Python CLI tool for extracting beat and tempo information from audio files. Currently optimized for Tabata workout synchronization.

## Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/bpm-analyzer.git
cd bpm-analyzer
pip install -e .

# Analyze an audio file (use librosa - currently the only working algorithm)
bpm-analyzer analyze test_audio.mp3 --algorithm librosa

# Get help
bpm-analyzer --help
```

## Current Status

✅ **Working**: Librosa algorithm, all output formats (JAMS/CSV/JSON), database operations, batch processing, comprehensive test suite  
❌ **Not Working**: Madmom algorithm (Python 3.12 incompatibility)  
⚠️ **Not Tested**: Essentia, Aubio, Ensemble algorithms

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed status.

## Installation

### Requirements
- Python 3.8+ (tested on 3.12.7)
- ffmpeg (optional, for MP3 support)

### Basic Install
```bash
pip install -e .
```

### Development Install
```bash
pip install -e ".[dev]"
pre-commit install  # Optional: setup code quality hooks
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bpm_analyzer

# Run specific test file
pytest tests/test_core_analyzer.py

# Run with verbose output
pytest -v
```

## Usage

### Analyze Single File
```bash
# Basic analysis
bpm-analyzer analyze song.mp3 --algorithm librosa

# Different output formats
bpm-analyzer analyze song.mp3 --algorithm librosa --format csv
bpm-analyzer analyze song.mp3 --algorithm librosa --format json

# Save to custom location
bpm-analyzer analyze song.mp3 --algorithm librosa --output results.jams
```

### Batch Processing
```bash
# Process directory
bpm-analyzer batch /path/to/music --algorithm librosa --output-dir ./results
```

### Database Operations
```bash
# Initialize database
bpm-analyzer db init

# Analyze and store
bpm-analyzer analyze song.mp3 --algorithm librosa --db sqlite:///music_tempo.db

# Query database
bpm-analyzer db query --min-bpm 100 --max-bpm 140
bpm-analyzer db stats
```

## Output Format

The tool outputs beat and tempo information in JAMS format by default:
- **Beat times**: Precise timestamps of each beat
- **Beat positions**: Position within measure (1-4 for 4/4 time)
- **Tempo**: BPM value(s) throughout the song
- **Confidence**: Algorithm confidence (currently fixed at 0.8 for librosa)

## Testing

This project includes a comprehensive test suite covering:

- **Unit Tests**: Individual components and functions
- **Integration Tests**: End-to-end workflows and component interactions
- **CLI Tests**: Command-line interface functionality
- **Database Tests**: Data persistence and querying
- **Algorithm Tests**: Beat detection implementations
- **Batch Processing Tests**: Multi-file processing scenarios

### Test Categories

- `test_core_analyzer.py` - Core analysis functionality
- `test_cli.py` - Command-line interface
- `test_database.py` - Database operations and models
- `test_algorithms.py` - Beat detection algorithms
- `test_utils.py` - Utility functions and validation
- `test_batch_processing.py` - Batch processing workflows
- `test_tempo_map.py` - Data structures and tempo mapping
- `test_config.py` - Configuration management
- `test_integration.py` - End-to-end integration scenarios

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=bmp_analyzer --cov-report=html

# Run specific test categories
pytest tests/test_core_analyzer.py -v
pytest tests/test_cli.py -k "test_analyze"

# Run integration tests only
pytest tests/test_integration.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `pytest` and ensure all tests pass
5. Add tests for new functionality
6. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Project Structure

```
bpm-analyzer/
├── bpm_analyzer/       # Main package
│   ├── algorithms/     # Beat detection algorithms
│   ├── core/          # Core analysis logic
│   ├── db/            # Database models
│   ├── processors/    # Batch processing
│   ├── utils/         # Utility functions
│   └── cli.py         # CLI interface
├── tests/             # Comprehensive test suite
│   ├── conftest.py    # Test fixtures and configuration
│   ├── test_*.py      # Test modules for each component
│   └── test_integration.py # End-to-end integration tests
├── docs/              # Documentation
└── test_audio.mp3     # Sample audio for testing
```

## License

MIT License - see [LICENSE](LICENSE) for details.