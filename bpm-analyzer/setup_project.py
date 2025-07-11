#!/usr/bin/env python3
"""
Setup script to create the complete BPM Analyzer project structure
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Define all directories to create
DIRECTORIES = [
    "bpm_analyzer/io",
    "bpm_analyzer/utils",
    "bpm_analyzer/processors",
    "bpm_analyzer/db",
    "tests",
    "tests/fixtures",
    "tests/unit",
    "tests/integration",
    "tests/data",
    "tests/data/sample_audio",
    "tests/data/expected",
    "scripts",
    "examples",
    "examples/notebooks",
    ".github",
    ".github/workflows",
    ".github/ISSUE_TEMPLATE",
]

# Create all directories
print("Creating directory structure...")
for dir_path in DIRECTORIES:
    full_path = BASE_DIR / dir_path
    full_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {dir_path}")

print("\nDirectory structure created successfully!")
print(f"Project location: {BASE_DIR}")
