# BPM Analyzer - Installation Guide

## Prerequisites

Before installing BPM Analyzer, ensure you have the following:

- Python 3.8 or higher
- pip (Python package manager)
- ffmpeg (for MP3 support)
- libsndfile (for soundfile)

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg libsndfile1
```

#### macOS
```bash
brew install ffmpeg libsndfile
```

#### Windows
1. Download ffmpeg from https://ffmpeg.org/download.html
2. Add ffmpeg to your PATH
3. libsndfile is included with soundfile Python package

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/bpm-analyzer.git
cd bpm-analyzer

# Install in development mode
pip install -e .
```

### Install with All Optional Dependencies

```bash
pip install -e ".[all]"
```

### Production Install

```bash
pip install bpm-analyzer
```

## Dependency Details

### Core Dependencies

- **numpy**: Numerical operations
- **madmom**: Primary beat detection algorithm
- **librosa**: Audio processing utilities
- **jams**: Annotation format
- **soundfile**: Fast audio I/O
- **pydub**: Format conversion
- **typer**: CLI framework
- **rich**: Beautiful terminal output
- **sqlalchemy**: Database support

### Optional Dependencies

- **essentia**: Alternative beat detection (requires separate installation)
- **aubio**: Lightweight beat detection
- **psycopg2-binary**: PostgreSQL support

## Installing Essentia

Essentia requires special installation steps:

### Ubuntu/Debian
```bash
sudo apt-get install build-essential libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev libavutil-dev libswresample-dev libsamplerate0-dev libtag1-dev libchromaprint-dev

pip install essentia
```

### macOS
```bash
brew install libyaml fftw ffmpeg chromaprint

pip install essentia
```

### Windows
Essentia on Windows requires building from source or using conda:
```bash
conda install -c conda-forge essentia
```

## Verifying Installation

After installation, verify everything is working:

```bash
# Check CLI is installed
bpm-analyzer --version

# Run info command
bpm-analyzer info

# Test with a sample file
bpm-analyzer analyze sample.mp3
```

## Troubleshooting

### Import Error: madmom
```bash
# Ensure Cython is installed
pip install cython
pip install --no-cache-dir madmom
```

### Import Error: soundfile
```bash
# On Linux, install system library
sudo apt-get install libsndfile1

# Reinstall soundfile
pip install --force-reinstall soundfile
```

### FFmpeg Not Found
Ensure ffmpeg is in your PATH:
```bash
# Check ffmpeg installation
ffmpeg -version

# Add to PATH if needed
export PATH="/path/to/ffmpeg/bin:$PATH"
```

### Permission Errors
Use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Docker Installation

For a containerized installation:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install BPM Analyzer
COPY . /app
WORKDIR /app
RUN pip install -e .

CMD ["bpm-analyzer", "--help"]
```

Build and run:
```bash
docker build -t bpm-analyzer .
docker run -v /path/to/music:/music bpm-analyzer analyze /music/song.mp3
```

## Development Setup

For development, install additional dependencies:

```bash
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black .

# Type check
mypy bpm_analyzer
```

## Next Steps

After installation:

1. Read the [Usage Guide](usage.md)
2. Check out [Examples](../examples/)
3. Configure settings in `~/.bpm_analyzer/config.yaml`
4. Start analyzing your music library!
