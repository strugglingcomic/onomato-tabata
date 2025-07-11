# BPM Analyzer CLI Tool - Project Plan

## Executive Summary

A Python CLI tool for analyzing audio files to generate detailed BPM/tempo maps suitable for Tabata workout synchronization. The tool will process individual audio files or batch collections, producing beat-by-beat timing data stored in standardized formats.

## Core Requirements

1. **Input**: Support MP3, WAV, FLAC, M4A, OGG formats
2. **Output**: Detailed tempo maps with beat-by-beat precision
3. **Storage**: JAMS format for rich annotations
4. **Performance**: Batch processing capability for building music databases
5. **Accuracy**: Beat timing precision within ±10ms for workout synchronization

## Architecture Decisions Required

### 🔧 Decision Point 1: Primary BPM Detection Strategy
**Options:**
- **A) madmom-first**: Use madmom as primary with essentia fallback
- **B) essentia-first**: Use essentia as primary with madmom for verification
- **C) ensemble**: Always run both and combine results
- **D) configurable**: Let user choose via CLI flags

**Recommendation**: Start with A (madmom-first) for highest accuracy

### 🔧 Decision Point 2: CLI Framework
**Options:**
- **A) click**: Full-featured, widely used, good plugin system
- **B) typer**: Modern, type-hints based, built on click
- **C) argparse**: Standard library, no dependencies
- **D) fire**: Google's auto-CLI from functions

**Recommendation**: B (typer) for modern Python practices

### 🔧 Decision Point 3: Audio Loading Strategy
**Options:**
- **A) librosa-primary**: Use librosa for all loading with audioread backend
- **B) soundfile-primary**: Use soundfile for WAV/FLAC, pydub for others
- **C) format-specific**: Different libraries optimized per format

**Recommendation**: B for performance with fallback to A

### 🔧 Decision Point 4: Processing Architecture
**Options:**
- **A) sequential**: Process files one at a time
- **B) multiprocessing**: Parallel processing with ProcessPoolExecutor
- **C) async**: Async I/O with sync processing
- **D) distributed**: Celery/Ray for large-scale processing

**Recommendation**: B for single-machine performance

### 🔧 Decision Point 5: Output Options
**Options:**
- **A) jams-only**: Only output JAMS format
- **B) multi-format**: JAMS + CSV/JSON export options
- **C) database**: Direct SQLite/PostgreSQL integration
- **D) api-ready**: Include REST API server mode

**Recommendation**: Start with B, consider D for v2

## Development Phases

### Phase 1: Core Functionality (Weeks 1-2)
- Basic CLI structure
- Single file BPM detection
- JAMS output format
- Basic error handling

### Phase 2: Robustness (Weeks 3-4)
- Multi-format audio support
- Batch processing
- Progress indicators
- Comprehensive error handling
- Logging system

### Phase 3: Advanced Features (Weeks 5-6)
- Ensemble BPM detection
- Confidence scoring
- Variable tempo tracking
- CSV/JSON export

### Phase 4: Optimization (Weeks 7-8)
- Parallel processing
- Caching system
- Performance profiling
- Memory optimization

### Phase 5: Polish & Extensions (Weeks 9-10)
- Comprehensive testing
- Documentation
- Docker packaging
- Example notebooks
- (Optional) REST API

## Technical Stack

### Core Dependencies
```
# Required
madmom>=0.16.1          # Primary BPM detection
jams>=0.3.4             # Annotation storage
librosa>=0.10.0         # Audio processing utilities
soundfile>=0.12.0       # Fast audio I/O
typer>=0.9.0           # CLI framework (pending decision)
numpy>=1.24.0          # Numerical operations
rich>=13.0.0           # Beautiful terminal output

# Optional/Alternative
essentia>=2.1b6         # Alternative BPM detection
aubio>=0.4.9           # Lightweight alternative
pydub>=0.25.1          # Format conversion
click>=8.1.0           # Alternative CLI (pending decision)

# Development
pytest>=7.4.0          # Testing
black>=23.0.0          # Code formatting
mypy>=1.5.0            # Type checking
pre-commit>=3.3.0      # Git hooks
```

## Performance Targets

- Single file processing: < 10% of audio duration
- Batch processing: > 100 files/minute on modern hardware
- Memory usage: < 500MB for typical audio files
- Accuracy: > 85% within ±3 BPM of ground truth

## Next Steps

1. **Finalize architecture decisions** (need your input on the 5 decision points)
2. **Set up repository structure** (ready to generate)
3. **Create initial CLI skeleton** (ready to generate)
4. **Implement core BPM detection** (madmom integration)
5. **Add JAMS output formatting**
6. **Build test suite with sample audio**