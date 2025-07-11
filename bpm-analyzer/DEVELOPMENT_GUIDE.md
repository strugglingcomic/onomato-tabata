# BPM Analyzer - Development Guide

## Current State

The BPM Analyzer is partially implemented with the librosa algorithm fully functional. This guide helps developers understand the codebase and continue development.

## Working Components

### Core Modules
- `cli.py` - Typer-based CLI with all commands implemented
- `config.py` - Configuration management 
- `core/analyzer.py` - Main analysis orchestration
- `core/tempo_map.py` - Beat and tempo data structures
- `algorithms/librosa_impl.py` - Working beat detection
- `db/models.py` & `db/database.py` - Database with relationships

### Tested Features
- Single file analysis: `bpm-analyzer analyze file.mp3 --algorithm librosa`
- Batch processing: `bpm-analyzer batch /folder --algorithm librosa`
- Database operations: `bpm-analyzer db init/query/stats`
- Output formats: JAMS (default), CSV, JSON

## Known Issues

### Madmom Algorithm
- **Problem**: Python 3.12 incompatibility
- **Errors**: 
  - `MutableSequence` import from collections (needs collections.abc)
  - NumPy 2.x compatibility issues
- **Workaround**: Use `--algorithm librosa` or Python 3.11 environment

### FFmpeg Warning
- **Problem**: pydub can't find ffmpeg
- **Impact**: Minor - MP3 files still process correctly
- **Fix**: Install ffmpeg (`brew install ffmpeg` on macOS)

## Development Setup

```bash
# Clone and setup
git clone <repo-url>
cd bpm-analyzer
python -m venv venv
source venv/bin/activate

# Install for development
pip install -e ".[dev]"

# Test it works
bpm-analyzer analyze test_audio.mp3 --algorithm librosa
```

## Code Structure

```
bpm_analyzer/
├── cli.py              # CLI commands (analyze, batch, db, info, validate)
├── config.py           # Configuration dataclasses
├── core/
│   ├── analyzer.py     # AudioAnalyzer class, AnalysisResult
│   └── tempo_map.py    # Beat, TempoMap classes
├── algorithms/
│   ├── base.py         # BeatDetector interface
│   └── librosa_impl.py # Working implementation
└── db/
    ├── models.py       # AudioFile, Analysis, Beat models
    └── database.py     # Database operations
```

## Key Implementation Notes

### Adding New Algorithms

1. Inherit from `BeatDetector` in `algorithms/base.py`
2. Implement `detect(audio_data) -> TempoMap` method
3. Register in `ALGORITHM_MAP` in the relevant files

Example:
```python
class NewDetector(BeatDetector):
    def detect(self, audio_data: AudioData) -> TempoMap:
        # Your implementation
        beats = [Beat(time=t, position=p, confidence=c) for ...]
        return TempoMap(beats=beats, average_bpm=bpm)
```

### Database Schema
- `AudioFile`: Stores file metadata
- `Analysis`: Links to AudioFile, stores algorithm and results  
- `Beat`: Individual beat times linked to Analysis

### Output Formats
- **JAMS**: Full annotation format (default)
- **CSV**: Simple time,position,confidence,bpm columns
- **JSON**: Structured data with metadata

## Testing

Currently no automated tests. To test manually:

```bash
# Test basic analysis
bpm-analyzer analyze test_audio.mp3 --algorithm librosa --verbose

# Test database
bpm-analyzer db init
bpm-analyzer analyze test_audio.mp3 --algorithm librosa --db sqlite:///music_tempo.db
bpm-analyzer db query --min-bpm 100 --max-bpm 120

# Test batch processing
mkdir test_batch && cp test_audio.mp3 test_batch/
bpm-analyzer batch test_batch --algorithm librosa
```

## Common Tasks

### Fix Import Errors
Most algorithm import errors are due to missing dependencies:
```bash
pip install librosa  # For librosa algorithm
pip install madmom   # For madmom (won't work on Python 3.12)
pip install essentia # For essentia algorithm
```

### Debug Analysis Issues
1. Use `--verbose` flag for detailed output
2. Check `~/.bpm_analyzer/logs/` for log files (if implemented)
3. Validate audio file first: `bpm-analyzer validate file.mp3`

### Database Issues
- For relationship errors, check eager loading in `database.py`
- For query errors, verify joins in `db query` command
- Reset database: `rm music_tempo.db && bpm-analyzer db init`

## Next Steps

1. **High Priority**
   - Add test suite with pytest
   - Fix or document madmom Python version requirements
   - Implement essentia algorithm

2. **Medium Priority**
   - Add caching for repeated analyses
   - Implement audio loading module properly
   - Add progress callbacks for long files

3. **Low Priority**
   - Add visualization features
   - Implement ensemble methods
   - Add real-time processing

## Resources

- [Librosa docs](https://librosa.org/doc/latest/index.html)
- [JAMS format](https://jams.readthedocs.io/)
- [Typer CLI](https://typer.tiangolo.com/)