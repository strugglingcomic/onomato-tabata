import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from concurrent.futures import Future

from bpm_analyzer.processors.batch import BatchProcessor, BatchResult
from bpm_analyzer.core.analyzer import AnalysisResult
from bpm_analyzer.core.tempo_map import Beat


class TestBatchResult:
    """Test BatchResult dataclass"""
    
    def test_init_success(self, temp_audio_file):
        """Test BatchResult initialization for successful processing"""
        mock_result = Mock(spec=AnalysisResult)
        
        result = BatchResult(
            file_path=temp_audio_file,
            success=True,
            result=mock_result
        )
        
        assert result.file_path == temp_audio_file
        assert result.success == True
        assert result.result == mock_result
        assert result.error is None
    
    def test_init_failure(self, temp_audio_file):
        """Test BatchResult initialization for failed processing"""
        result = BatchResult(
            file_path=temp_audio_file,
            success=False,
            error="Processing failed"
        )
        
        assert result.file_path == temp_audio_file
        assert result.success == False
        assert result.result is None
        assert result.error == "Processing failed"


class TestBatchProcessor:
    """Test BatchProcessor class"""
    
    def test_init_default(self):
        """Test BatchProcessor initialization with defaults"""
        processor = BatchProcessor()
        
        assert processor.algorithm == "madmom"
        assert processor.output_format == "jams"
        assert processor.parallel == True
        assert processor.num_workers > 0
        assert processor.skip_existing == True
        assert processor.database_url is None
        assert processor.db is None
        assert processor.skipped_count == 0
    
    def test_init_custom(self):
        """Test BatchProcessor initialization with custom parameters"""
        processor = BatchProcessor(
            algorithm="librosa",
            output_format="csv",
            parallel=False,
            num_workers=2,
            skip_existing=False,
            database_url="sqlite:///test.db"
        )
        
        assert processor.algorithm == "librosa"
        assert processor.output_format == "csv"
        assert processor.parallel == False
        assert processor.num_workers == 2
        assert processor.skip_existing == False
        assert processor.database_url == "sqlite:///test.db"
        assert processor.db is not None
    
    def test_find_audio_files_non_recursive(self, temp_output_dir):
        """Test finding audio files without recursion"""
        processor = BatchProcessor()
        
        # Create test files
        (temp_output_dir / "song1.mp3").touch()
        (temp_output_dir / "song2.wav").touch()
        (temp_output_dir / "song3.flac").touch()
        (temp_output_dir / "readme.txt").touch()
        
        # Create subdirectory with audio file
        subdir = temp_output_dir / "subdir"
        subdir.mkdir()
        (subdir / "song4.mp3").touch()
        
        files = list(processor.find_audio_files(temp_output_dir, recursive=False))
        
        # Should find 3 audio files in main directory
        assert len(files) == 3
        filenames = [f.name for f in files]
        assert "song1.mp3" in filenames
        assert "song2.wav" in filenames
        assert "song3.flac" in filenames
        assert "song4.mp3" not in filenames  # In subdirectory
        assert "readme.txt" not in filenames  # Not audio
    
    def test_find_audio_files_recursive(self, temp_output_dir):
        """Test finding audio files with recursion"""
        processor = BatchProcessor()
        
        # Create test files
        (temp_output_dir / "song1.mp3").touch()
        (temp_output_dir / "song2.wav").touch()
        
        # Create subdirectory with audio file
        subdir = temp_output_dir / "subdir"
        subdir.mkdir()
        (subdir / "song3.flac").touch()
        (subdir / "song4.m4a").touch()
        
        files = list(processor.find_audio_files(temp_output_dir, recursive=True))
        
        # Should find 4 audio files including subdirectory
        assert len(files) == 4
        filenames = [f.name for f in files]
        assert "song1.mp3" in filenames
        assert "song2.wav" in filenames
        assert "song3.flac" in filenames
        assert "song4.m4a" in filenames
    
    def test_find_audio_files_with_pattern(self, temp_output_dir):
        """Test finding audio files with pattern"""
        processor = BatchProcessor()
        
        # Create test files
        (temp_output_dir / "song1.mp3").touch()
        (temp_output_dir / "song2.wav").touch()
        (temp_output_dir / "music3.mp3").touch()
        
        files = list(processor.find_audio_files(temp_output_dir, pattern="song*", recursive=False))
        
        # Should find only files matching pattern
        assert len(files) == 2
        filenames = [f.name for f in files]
        assert "song1.mp3" in filenames
        assert "song2.wav" in filenames
        assert "music3.mp3" not in filenames
    
    def test_find_audio_files_supported_extensions(self, temp_output_dir):
        """Test finding files with supported audio extensions"""
        processor = BatchProcessor()
        
        # Create files with various extensions
        (temp_output_dir / "song.mp3").touch()
        (temp_output_dir / "song.wav").touch()
        (temp_output_dir / "song.flac").touch()
        (temp_output_dir / "song.m4a").touch()
        (temp_output_dir / "song.ogg").touch()
        (temp_output_dir / "song.aac").touch()  # Not supported
        (temp_output_dir / "song.wma").touch()  # Not supported
        
        files = list(processor.find_audio_files(temp_output_dir, recursive=False))
        
        # Should find only supported formats
        assert len(files) == 5
        extensions = [f.suffix.lower() for f in files]
        assert '.mp3' in extensions
        assert '.wav' in extensions
        assert '.flac' in extensions
        assert '.m4a' in extensions
        assert '.ogg' in extensions
        assert '.aac' not in extensions
        assert '.wma' not in extensions
    
    def test_get_output_path(self, temp_output_dir):
        """Test getting output path for input file"""
        processor = BatchProcessor(output_format="csv")
        
        input_file = Path("/input/dir/song.mp3")
        output_path = processor._get_output_path(input_file, temp_output_dir)
        
        expected_path = temp_output_dir / "song.csv"
        assert output_path == expected_path
    
    def test_get_output_path_different_formats(self, temp_output_dir):
        """Test getting output path with different formats"""
        input_file = Path("/input/dir/song.mp3")
        
        # Test JAMS format
        processor_jams = BatchProcessor(output_format="jams")
        output_jams = processor_jams._get_output_path(input_file, temp_output_dir)
        assert output_jams.suffix == ".jams"
        
        # Test JSON format
        processor_json = BatchProcessor(output_format="json")
        output_json = processor_json._get_output_path(input_file, temp_output_dir)
        assert output_json.suffix == ".json"
    
    @patch('bpm_analyzer.processors.batch.analyze_file')
    def test_process_single_file_success(self, mock_analyze_file, temp_output_dir):
        """Test successful processing of single file"""
        processor = BatchProcessor(output_format="jams")
        
        # Mock analysis result
        mock_result = Mock(spec=AnalysisResult)
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        input_file = Path("/input/song.mp3")
        result = processor._process_single_file(input_file, temp_output_dir)
        
        assert result.success == True
        assert result.file_path == input_file
        assert result.result == mock_result
        assert result.error is None
        
        mock_analyze_file.assert_called_once()
        mock_result.save.assert_called_once()
    
    @patch('bpm_analyzer.processors.batch.analyze_file')
    def test_process_single_file_skip_existing(self, mock_analyze_file, temp_output_dir):
        """Test skipping file when output already exists"""
        processor = BatchProcessor(skip_existing=True)
        
        input_file = Path("/input/song.mp3")
        output_file = temp_output_dir / "song.jams"
        output_file.touch()  # Create existing output file
        
        result = processor._process_single_file(input_file, temp_output_dir)
        
        assert result.success == True
        assert result.file_path == input_file
        assert result.result is None
        assert "Skipped" in result.error
        assert processor.skipped_count == 1
        
        mock_analyze_file.assert_not_called()
    
    @patch('bpm_analyzer.processors.batch.analyze_file')
    def test_process_single_file_no_skip_existing(self, mock_analyze_file, temp_output_dir):
        """Test processing file even when output exists"""
        processor = BatchProcessor(skip_existing=False)
        
        # Mock analysis result
        mock_result = Mock(spec=AnalysisResult)
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        input_file = Path("/input/song.mp3")
        output_file = temp_output_dir / "song.jams"
        output_file.touch()  # Create existing output file
        
        result = processor._process_single_file(input_file, temp_output_dir)
        
        assert result.success == True
        assert result.file_path == input_file
        assert result.result == mock_result
        assert processor.skipped_count == 0
        
        mock_analyze_file.assert_called_once()
        mock_result.save.assert_called_once()
    
    @patch('bpm_analyzer.processors.batch.analyze_file')
    def test_process_single_file_with_database(self, mock_analyze_file, temp_output_dir):
        """Test processing file with database storage"""
        mock_db = Mock()
        processor = BatchProcessor(database_url="sqlite:///test.db")
        processor.db = mock_db
        
        # Mock analysis result
        mock_result = Mock(spec=AnalysisResult)
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        input_file = Path("/input/song.mp3")
        result = processor._process_single_file(input_file, temp_output_dir)
        
        assert result.success == True
        mock_db.store_analysis.assert_called_once_with(mock_result)
    
    @patch('bpm_analyzer.processors.batch.analyze_file')
    def test_process_single_file_error(self, mock_analyze_file, temp_output_dir):
        """Test processing file with error"""
        processor = BatchProcessor()
        
        # Mock analysis failure
        mock_analyze_file.side_effect = Exception("Analysis failed")
        
        input_file = Path("/input/song.mp3")
        result = processor._process_single_file(input_file, temp_output_dir)
        
        assert result.success == False
        assert result.file_path == input_file
        assert result.result is None
        assert "Analysis failed" in result.error
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor._process_sequential')
    def test_process_files_sequential(self, mock_process_sequential, temp_output_dir):
        """Test processing files sequentially"""
        processor = BatchProcessor(parallel=False)
        
        files = [Path("file1.mp3"), Path("file2.mp3")]
        mock_results = [Mock(), Mock()]
        mock_process_sequential.return_value = mock_results
        
        results = processor.process_files(files, temp_output_dir)
        
        assert results == mock_results
        mock_process_sequential.assert_called_once_with(files, temp_output_dir)
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor._process_sequential')
    def test_process_files_sequential_single_file(self, mock_process_sequential, temp_output_dir):
        """Test processing single file uses sequential processing"""
        processor = BatchProcessor(parallel=True)  # Even with parallel=True
        
        files = [Path("file1.mp3")]  # Single file
        mock_results = [Mock()]
        mock_process_sequential.return_value = mock_results
        
        results = processor.process_files(files, temp_output_dir)
        
        assert results == mock_results
        mock_process_sequential.assert_called_once_with(files, temp_output_dir)
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor._process_parallel')
    def test_process_files_parallel(self, mock_process_parallel, temp_output_dir):
        """Test processing files in parallel"""
        processor = BatchProcessor(parallel=True)
        
        files = [Path("file1.mp3"), Path("file2.mp3")]
        mock_results = [Mock(), Mock()]
        mock_process_parallel.return_value = mock_results
        
        results = processor.process_files(files, temp_output_dir)
        
        assert results == mock_results
        mock_process_parallel.assert_called_once_with(files, temp_output_dir)
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor._process_single_file')
    def test_process_sequential(self, mock_process_single, temp_output_dir):
        """Test sequential processing implementation"""
        processor = BatchProcessor()
        
        files = [Path("file1.mp3"), Path("file2.mp3")]
        mock_results = [
            BatchResult(file_path=files[0], success=True),
            BatchResult(file_path=files[1], success=True)
        ]
        mock_process_single.side_effect = mock_results
        
        results = processor._process_sequential(files, temp_output_dir)
        
        assert len(results) == 2
        assert results == mock_results
        assert mock_process_single.call_count == 2
    
    @patch('bpm_analyzer.processors.batch.ProcessPoolExecutor')
    @patch('bpm_analyzer.processors.batch.BatchProcessor._process_single_file')
    def test_process_parallel(self, mock_process_single, mock_executor_class, temp_output_dir):
        """Test parallel processing implementation"""
        processor = BatchProcessor(num_workers=2)
        
        # Mock executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures
        future1 = Mock()
        future2 = Mock()
        future1.result.return_value = BatchResult(file_path=Path("file1.mp3"), success=True)
        future2.result.return_value = BatchResult(file_path=Path("file2.mp3"), success=True)
        
        mock_executor.submit.side_effect = [future1, future2]
        
        # Mock as_completed
        with patch('bpm_analyzer.processors.batch.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [future1, future2]
            
            files = [Path("file1.mp3"), Path("file2.mp3")]
            results = processor._process_parallel(files, temp_output_dir)
            
            assert len(results) == 2
            assert mock_executor.submit.call_count == 2
            mock_executor_class.assert_called_once_with(max_workers=2)
    
    @patch('bpm_analyzer.processors.batch.ProcessPoolExecutor')
    def test_process_parallel_with_exception(self, mock_executor_class, temp_output_dir):
        """Test parallel processing with exception handling"""
        processor = BatchProcessor()
        
        # Mock executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock future that raises exception
        future = Mock()
        future.result.side_effect = Exception("Processing error")
        mock_executor.submit.return_value = future
        
        # Mock as_completed
        with patch('bpm_analyzer.processors.batch.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [future]
            
            files = [Path("file1.mp3")]
            results = processor._process_parallel(files, temp_output_dir)
            
            assert len(results) == 1
            assert results[0].success == False
            assert "Processing error" in results[0].error


class TestBatchProcessorIntegration:
    """Integration tests for batch processing"""
    
    def test_batch_processor_end_to_end(self, temp_output_dir):
        """Test complete batch processing workflow"""
        processor = BatchProcessor(
            algorithm="librosa",
            output_format="json",
            parallel=False,
            skip_existing=False
        )
        
        # Create test audio files
        input_dir = temp_output_dir / "input"
        input_dir.mkdir()
        
        audio_files = []
        for i in range(3):
            audio_file = input_dir / f"song{i}.mp3"
            audio_file.touch()
            audio_files.append(audio_file)
        
        # Create output directory
        output_dir = temp_output_dir / "output"
        output_dir.mkdir()
        
        # Mock analyze_file to avoid actual audio processing
        with patch('bpm_analyzer.processors.batch.analyze_file') as mock_analyze:
            mock_result = Mock(spec=AnalysisResult)
            mock_result.save = Mock()
            mock_analyze.return_value = mock_result
            
            # Find files
            found_files = list(processor.find_audio_files(input_dir))
            assert len(found_files) == 3
            
            # Process files
            results = processor.process_files(found_files, output_dir)
            
            # Verify results
            assert len(results) == 3
            assert all(r.success for r in results)
            assert mock_analyze.call_count == 3
            assert mock_result.save.call_count == 3
    
    def test_batch_processor_with_mixed_results(self, temp_output_dir):
        """Test batch processing with mixed success/failure"""
        processor = BatchProcessor(parallel=False)
        
        # Create test files
        input_dir = temp_output_dir / "input"
        input_dir.mkdir()
        
        file1 = input_dir / "good.mp3"
        file2 = input_dir / "bad.mp3"
        file1.touch()
        file2.touch()
        
        output_dir = temp_output_dir / "output"
        output_dir.mkdir()
        
        # Mock analyze_file to simulate mixed results
        with patch('bpm_analyzer.processors.batch.analyze_file') as mock_analyze:
            def analyze_side_effect(file_path, config):
                if "good" in str(file_path):
                    mock_result = Mock(spec=AnalysisResult)
                    mock_result.save = Mock()
                    return mock_result
                else:
                    raise Exception("Analysis failed")
            
            mock_analyze.side_effect = analyze_side_effect
            
            files = [file1, file2]
            results = processor.process_files(files, output_dir)
            
            # Should have one success and one failure
            assert len(results) == 2
            successes = [r for r in results if r.success]
            failures = [r for r in results if not r.success]
            
            assert len(successes) == 1
            assert len(failures) == 1
            assert "good" in str(successes[0].file_path)
            assert "bad" in str(failures[0].file_path)
    
    def test_batch_processor_skip_existing_integration(self, temp_output_dir):
        """Test batch processing with existing output files"""
        processor = BatchProcessor(skip_existing=True, parallel=False)
        
        # Create input files
        input_dir = temp_output_dir / "input"
        input_dir.mkdir()
        
        file1 = input_dir / "song1.mp3"
        file2 = input_dir / "song2.mp3"
        file1.touch()
        file2.touch()
        
        # Create output directory with existing output for file1
        output_dir = temp_output_dir / "output"
        output_dir.mkdir()
        (output_dir / "song1.jams").touch()
        
        # Mock analyze_file
        with patch('bpm_analyzer.processors.batch.analyze_file') as mock_analyze:
            mock_result = Mock(spec=AnalysisResult)
            mock_result.save = Mock()
            mock_analyze.return_value = mock_result
            
            files = [file1, file2]
            results = processor.process_files(files, output_dir)
            
            # Should have one skipped and one processed
            assert len(results) == 2
            assert all(r.success for r in results)
            assert processor.skipped_count == 1
            
            # Only file2 should be analyzed (file1 was skipped)
            assert mock_analyze.call_count == 1
            analyzed_file = mock_analyze.call_args[0][0]
            assert "song2" in str(analyzed_file)