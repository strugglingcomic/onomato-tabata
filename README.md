# Onomato Tabata

A comprehensive workout application suite designed for rhythm-based fitness, particularly Tabata training with musical synchronization.

## Project Overview

Onomato Tabata is being developed as a multi-component application that combines music analysis with workout timing to create synchronized fitness experiences. The project aims to provide:

- **Intelligent workout timing** based on musical beats and tempo
- **Tabata-specific training modes** with automatic interval management
- **Audio analysis capabilities** for beat detection and tempo mapping
- **Flexible workout customization** with musical synchronization

## Architecture

This repository contains multiple components:

### Backend Components
- **[bpm-analyzer/](bpm-analyzer/)** - Python CLI tool for extracting beat and tempo information from audio files
  - Supports multiple algorithms (Librosa, Madmom, Essentia, Aubio)
  - Outputs structured beat data in JAMS/CSV/JSON formats
  - Batch processing and database storage capabilities

### Planned Components
- **Frontend Application** - User interface for workout configuration and execution
- **Workout Engine** - Core logic for managing Tabata intervals and musical synchronization
- **Audio Processing Service** - Real-time audio analysis and beat tracking
- **User Management** - Profile, preferences, and workout history

## Current Status

🚧 **Early Development Phase**

- ✅ BPM analysis backend (functional with Librosa)
- ⚠️ Frontend and workout engine (planning phase)
- ⚠️ Real-time audio processing (not started)

## Quick Start

Currently, only the BPM analyzer component is available:

```bash
# Navigate to the BPM analyzer
cd bpm-analyzer

# Install dependencies
pip install -e .

# Analyze an audio file
bpm-analyzer analyze your-song.mp3 --algorithm librosa
```

## Vision

The ultimate goal is to create a workout application that:
1. Analyzes your music library for tempo and beat patterns
2. Generates Tabata routines synchronized to your favorite songs
3. Provides real-time workout guidance with musical cues
4. Tracks workout performance and musical preferences

## Contributing

This project is in active development. Each component will have its own contributing guidelines as they mature.

## License

MIT License - see individual component licenses for details.