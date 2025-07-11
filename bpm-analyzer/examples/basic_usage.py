#!/usr/bin/env python3
"""
Basic usage example for BPM Analyzer
"""
from pathlib import Path
from bpm_analyzer import analyze_audio, AnalysisConfig

def main():
    # Example 1: Analyze a single file with default settings
    print("Example 1: Basic analysis")
    print("-" * 40)
    
    audio_file = Path("sample.mp3")
    if audio_file.exists():
        result = analyze_audio(audio_file)
        print(f"File: {audio_file}")
        print(f"Average BPM: {result.average_bpm:.1f}")
        print(f"Number of beats: {len(result.beats)}")
        print(f"Duration: {result.duration:.1f} seconds")
        print()
    else:
        print(f"Sample file '{audio_file}' not found")
        print()
    
    # Example 2: Analyze with specific algorithm
    print("Example 2: Using specific algorithm")
    print("-" * 40)
    
    if audio_file.exists():
        config = AnalysisConfig(
            algorithm="librosa",
            confidence_threshold=0.8,
            tempo_range=(60, 180)
        )
        result = analyze_audio(audio_file, config=config)
        print(f"Algorithm: {result.algorithm}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print()
    
    # Example 3: Save results in different formats
    print("Example 3: Saving results")
    print("-" * 40)
    
    if audio_file.exists():
        result = analyze_audio(audio_file)
        
        # Save as JAMS
        result.save("output.jams", format="jams")
        print("Saved as JAMS: output.jams")
        
        # Save as CSV
        result.save("output.csv", format="csv")
        print("Saved as CSV: output.csv")
        
        # Save as JSON
        result.save("output.json", format="json")
        print("Saved as JSON: output.json")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
