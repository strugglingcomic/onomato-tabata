# Testing Guide

This document provides comprehensive information about the test suite for the BPM Analyzer project.

## Overview

The BPM Analyzer includes a comprehensive test suite designed to ensure reliability, maintainability, and correctness of all components. The test suite covers unit tests, integration tests, and end-to-end scenarios.

## Test Structure

```
tests/
├── conftest.py              # Test fixtures and configuration
├── test_core_analyzer.py    # Core analysis functionality
├── test_cli.py              # Command-line interface
├── test_database.py         # Database operations and models
├── test_algorithms.py       # Beat detection algorithms
├── test_utils.py            # Utility functions and validation
├── test_batch_processing.py # Batch processing workflows
├── test_tempo_map.py        # Data structures and tempo mapping
├── test_config.py           # Configuration management
└── test_integration.py      # End-to-end integration scenarios
```

## Test Categories

### Unit Tests

**Purpose**: Test individual components and functions in isolation.

- **test_core_analyzer.py**: Tests for `AnalysisResult`, `AudioAnalyzer`, and analysis functions
- **test_tempo_map.py**: Tests for `Beat` and `TempoMap` data structures
- **test_config.py**: Tests for configuration management and validation
- **test_algorithms.py**: Tests for beat detection algorithm implementations
- **test_utils.py**: Tests for utility functions, validation, and logging
- **test_database.py**: Tests for database models and operations

### Integration Tests

**Purpose**: Test component interactions and workflows.

- **test_cli.py**: Tests for CLI commands and argument parsing
- **test_batch_processing.py**: Tests for multi-file processing workflows
- **test_integration.py**: End-to-end scenarios and real-world usage patterns

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_core_analyzer.py

# Run tests matching a pattern
pytest -k "test_analyze"
```

### Coverage Reporting

```bash
# Run with coverage
pytest --cov=bpm_analyzer

# Generate HTML coverage report
pytest --cov=bpm_analyzer --cov-report=html

# Generate detailed coverage report
pytest --cov=bpm_analyzer --cov-report=term-missing
```

### Test Selection

```bash
# Run only unit tests
pytest tests/test_core_analyzer.py tests/test_tempo_map.py tests/test_config.py

# Run only integration tests
pytest tests/test_integration.py

# Run CLI tests only
pytest tests/test_cli.py

# Run database tests only
pytest tests/test_database.py
```

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py` to provide consistent test data:

### Audio Data Fixtures

- `sample_audio_data`: Mock audio data for testing
- `temp_audio_file`: Temporary audio file for file operations
- `sample_beats`: Sample beat data for tempo map testing

### Configuration Fixtures

- `sample_analysis_config`: Standard analysis configuration
- `sample_tempo_map`: Sample tempo map with beats and metadata

### Database Fixtures

- `temp_db`: Temporary database for testing persistence
- `temp_output_dir`: Temporary directory for output files

### Mock Fixtures

- `mock_librosa`: Mock librosa library for algorithm testing
- `mock_audio_loader`: Mock audio loading functionality

## Test Patterns

### Mocking External Dependencies

The test suite uses mocking to isolate components and avoid external dependencies:

```python
@patch('bpm_analyzer.algorithms.librosa_impl.librosa')
def test_librosa_detection(mock_librosa):
    mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
    mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
    
    # Test implementation
```

### Parametrized Tests

Complex scenarios use parametrized tests for comprehensive coverage:

```python
@pytest.mark.parametrize("algorithm,expected_bpm", [
    ("librosa", 120.0),
    ("madmom", 125.0),
])
def test_algorithm_detection(algorithm, expected_bpm):
    # Test implementation
```

### Temporary File Management

Tests that require files use temporary directories with automatic cleanup:

```python
def test_file_operations(temp_output_dir):
    output_file = temp_output_dir / "test.jams"
    # File operations
    assert output_file.exists()
    # Cleanup happens automatically
```

## Test Data

### Sample Audio

The test suite includes sample audio data and fixtures:

- Mock audio data with realistic properties
- Temporary audio files for integration testing
- Sample beat and tempo data for algorithm testing

### Expected Outputs

Tests include expected outputs for validation:

- JAMS format annotations
- CSV and JSON export formats
- Database query results
- CLI command outputs

## Error Testing

The test suite includes comprehensive error testing:

### Exception Handling

```python
def test_invalid_input():
    with pytest.raises(ValueError, match="Invalid input"):
        analyze_invalid_file()
```

### Error Recovery

```python
def test_partial_failure_recovery():
    # Test scenarios where some operations fail
    # but the system recovers gracefully
```

### Validation Testing

```python
def test_input_validation():
    # Test various invalid inputs
    # Ensure proper error messages
```

## Performance Considerations

### Fast Test Execution

- Mock external dependencies (librosa, file I/O)
- Use in-memory databases for testing
- Minimal test data sizes
- Parallel test execution where possible

### Resource Management

- Proper cleanup of temporary files
- Memory-efficient test data
- Database connection management
- Mock object cleanup

## Continuous Integration

The test suite is designed for CI/CD environments:

### Test Configuration

```bash
# CI-friendly test execution
pytest --tb=short --disable-warnings

# With coverage for CI
pytest --cov=bpm_analyzer --cov-report=xml
```

### Environment Variables

Tests respect environment variables for configuration:

- `PYTEST_CURRENT_TEST`: Current test identification
- `CI`: CI environment detection
- Test-specific configuration overrides

## Adding New Tests

### Test File Naming

- Use `test_*.py` pattern for test files
- Match test file names to source modules
- Group related tests in classes

### Test Function Naming

- Use descriptive test names: `test_analyze_file_with_invalid_format`
- Include setup and expected outcome: `test_database_query_returns_correct_results`
- Use parametrized tests for multiple scenarios

### Test Structure

```python
def test_feature_description():
    # Arrange: Setup test data
    config = AnalysisConfig(algorithm="librosa")
    
    # Act: Execute the functionality
    result = analyze_file(audio_file, config)
    
    # Assert: Verify expectations
    assert result.average_bpm == 120.0
    assert len(result.beats) > 0
```

## Test Maintenance

### Regular Updates

- Update tests when adding new features
- Maintain test data consistency
- Update mock objects with API changes
- Review and update test documentation

### Test Quality

- Ensure tests are deterministic
- Avoid test interdependencies
- Use clear assertions with descriptive messages
- Maintain good test coverage (>95%)

## Troubleshooting

### Common Issues

1. **ImportError**: Ensure development dependencies are installed
2. **FileNotFoundError**: Check temporary file creation and cleanup
3. **Mock failures**: Verify mock configurations match actual APIs
4. **Database errors**: Ensure proper database fixture usage

### Debug Mode

```bash
# Run tests with debugging
pytest --pdb

# Run with print statements
pytest -s

# Run single test with verbose output
pytest tests/test_core_analyzer.py::test_specific_function -v
```

## Test Coverage Goals

The test suite aims for:

- **Overall coverage**: >95%
- **Critical paths**: 100% coverage
- **Error handling**: Complete exception testing
- **Integration scenarios**: All major workflows tested
- **CLI commands**: All commands and options tested

## Contributing to Tests

When contributing to the project:

1. **Write tests first**: Follow TDD practices
2. **Test new features**: All new functionality must have tests
3. **Update existing tests**: Modify tests when changing behavior
4. **Run full test suite**: Ensure all tests pass before submitting
5. **Add integration tests**: Test how components work together

## Test Environment Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest --version
pytest tests/ -v

# Generate coverage report
pytest --cov=bpm_analyzer --cov-report=html
open htmlcov/index.html  # View coverage report
```

The comprehensive test suite ensures the BPM Analyzer maintains high quality and reliability across all components and usage scenarios.