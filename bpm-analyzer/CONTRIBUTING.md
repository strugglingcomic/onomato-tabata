# Contributing to BPM Analyzer

Thank you for your interest in contributing! This guide will help you get started.

## Quick Start

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make changes and test them
5. Submit a pull request

## Development Setup

```bash
# Clone the repo
git clone <repo-url>
cd bpm-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Verify installation
bpm-analyzer --help
```

## Current State

- ✅ **Working**: Librosa algorithm, CLI, database, all output formats
- ❌ **Broken**: Madmom algorithm (Python 3.12 incompatibility)
- ⚠️ **Untested**: Essentia, Aubio algorithms

Test with: `bpm-analyzer analyze test_audio.mp3 --algorithm librosa`

## Code Style

- Use [Black](https://github.com/psf/black) for formatting: `black .`
- Add type hints to all functions
- Follow PEP 8 guidelines
- Write clear docstrings for public APIs

Example:
```python
def analyze_file(
    audio_path: Path,
    config: Optional[AnalysisConfig] = None
) -> AnalysisResult:
    """Analyze an audio file for BPM and beat information.
    
    Args:
        audio_path: Path to the audio file
        config: Optional configuration
        
    Returns:
        AnalysisResult with tempo and beat data
    """
```

## Testing

Currently no automated tests. Test manually:

```bash
# Basic functionality
bpm-analyzer analyze test_audio.mp3 --algorithm librosa

# Database operations
bpm-analyzer db init
bpm-analyzer analyze test_audio.mp3 --algorithm librosa --db sqlite:///test.db
bpm-analyzer db query --min-bpm 100 --max-bpm 140

# Batch processing
bpm-analyzer batch ./test_batch --algorithm librosa
```

## Pull Request Guidelines

1. **Update documentation** if you change functionality
2. **Test your changes** thoroughly
3. **Keep PRs focused** - one feature/fix per PR
4. **Write clear commit messages**
5. **Update PROJECT_STATUS.md** if you fix issues or add features

## Reporting Issues

When reporting bugs, include:
- Python version and OS
- Full error message/traceback
- Steps to reproduce
- Expected vs actual behavior

## Priority Areas

Help wanted with:
1. Adding pytest test suite
2. Fixing madmom Python 3.12 compatibility
3. Testing/implementing essentia and aubio algorithms
4. Improving error messages and handling
5. Adding audio file loading robustness

## Questions?

Open an issue for questions or discussions about the codebase.