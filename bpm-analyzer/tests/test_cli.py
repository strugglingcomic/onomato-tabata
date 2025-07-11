import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import csv
import json
from typer.testing import CliRunner

from bpm_analyzer.cli import app, Algorithm, OutputFormat
from bpm_analyzer.core.analyzer import AnalysisResult
from bpm_analyzer.core.tempo_map import Beat


class TestCLI:
    """Test CLI interface"""
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test help command"""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "BPM Analyzer" in result.stdout
        assert "analyze" in result.stdout
        assert "batch" in result.stdout
        assert "db" in result.stdout
    
    def test_version_command(self):
        """Test version command"""
        with patch('bpm_analyzer.version.__version__', '0.1.0'):
            result = self.runner.invoke(app, ["--version"])
            
            assert result.exit_code == 0
            assert "0.1.0" in result.stdout
    
    def test_info_command(self):
        """Test info command"""
        result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "Available Algorithms" in result.stdout
        assert "madmom" in result.stdout
        assert "librosa" in result.stdout
        assert "Output Formats" in result.stdout
        assert "jams" in result.stdout


class TestAnalyzeCommand:
    """Test analyze command"""
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_basic(self, mock_analyze_file, temp_audio_file):
        """Test basic analyze command"""
        # Mock the analysis result
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = [Beat(time=0.5, position=1, confidence=0.9)]
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--algorithm", "librosa",
            "--format", "jams"
        ])
        
        assert result.exit_code == 0
        assert "Analysis complete" in result.stdout
        assert "120.0" in result.stdout
        assert "1" in result.stdout  # beat count
        assert "5.0s" in result.stdout  # duration
        
        mock_analyze_file.assert_called_once()
        mock_result.save.assert_called_once()
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_with_output_file(self, mock_analyze_file, temp_audio_file, temp_output_dir):
        """Test analyze command with custom output file"""
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = []
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        output_file = temp_output_dir / "custom_output.jams"
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--output", str(output_file),
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 0
        mock_result.save.assert_called_once_with(output_file, format="jams")
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_csv_format(self, mock_analyze_file, temp_audio_file):
        """Test analyze command with CSV output"""
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = []
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--format", "csv",
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 0
        
        # Check that save was called with CSV format
        args, kwargs = mock_result.save.call_args
        assert kwargs['format'] == "csv"
        assert args[0].suffix == ".csv"
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_json_format(self, mock_analyze_file, temp_audio_file):
        """Test analyze command with JSON output"""
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = []
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--format", "json",
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 0
        
        # Check that save was called with JSON format
        args, kwargs = mock_result.save.call_args
        assert kwargs['format'] == "json"
        assert args[0].suffix == ".json"
    
    @patch('bpm_analyzer.cli.analyze_file')
    @patch('bpm_analyzer.db.database.AnalysisDB')
    def test_analyze_with_database(self, mock_db_class, mock_analyze_file, temp_audio_file):
        """Test analyze command with database storage"""
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = []
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--db", "sqlite:///test.db",
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 0
        assert "Stored in database" in result.stdout
        
        mock_db_class.assert_called_once_with("sqlite:///test.db")
        mock_db.store_analysis.assert_called_once_with(mock_result)
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_with_confidence_threshold(self, mock_analyze_file, temp_audio_file):
        """Test analyze command with confidence threshold"""
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = []
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--confidence", "0.7",
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 0
        
        # Check that analyze_file was called with correct config
        args, kwargs = mock_analyze_file.call_args
        config = args[1]
        assert config.confidence_threshold == 0.7
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_with_tempo_range(self, mock_analyze_file, temp_audio_file):
        """Test analyze command with tempo range"""
        mock_result = Mock(spec=AnalysisResult)
        mock_result.average_bpm = 120.0
        mock_result.beats = []
        mock_result.duration = 5.0
        mock_result.save = Mock()
        mock_analyze_file.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--tempo-min", "80",
            "--tempo-max", "160",
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 0
        
        # Check that analyze_file was called with correct config
        args, kwargs = mock_analyze_file.call_args
        config = args[1]
        assert config.tempo_range == (80, 160)
    
    @patch('bpm_analyzer.cli.analyze_file')
    def test_analyze_error_handling(self, mock_analyze_file, temp_audio_file):
        """Test analyze command error handling"""
        mock_analyze_file.side_effect = Exception("Analysis failed")
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code == 1
        assert "Error: Analysis failed" in result.stdout
    
    def test_analyze_nonexistent_file(self):
        """Test analyze command with non-existent file"""
        result = self.runner.invoke(app, [
            "analyze",
            "/nonexistent/file.mp3",
            "--algorithm", "librosa"
        ])
        
        assert result.exit_code != 0


class TestBatchCommand:
    """Test batch command"""
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor')
    def test_batch_basic(self, mock_batch_processor_class, temp_output_dir):
        """Test basic batch command"""
        mock_processor = Mock()
        mock_processor.find_audio_files.return_value = [Path("test1.mp3"), Path("test2.mp3")]
        mock_processor.process_files.return_value = [
            Mock(success=True),
            Mock(success=True)
        ]
        mock_processor.skipped_count = 0
        mock_batch_processor_class.return_value = mock_processor
        
        with tempfile.TemporaryDirectory() as input_dir:
            result = self.runner.invoke(app, [
                "batch",
                input_dir,
                "--output-dir", str(temp_output_dir),
                "--algorithm", "librosa"
            ])
        
        assert result.exit_code == 0
        assert "Found 2 audio files" in result.stdout
        assert "Successful" in result.stdout
        assert "2" in result.stdout
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor')
    def test_batch_with_pattern(self, mock_batch_processor_class, temp_output_dir):
        """Test batch command with file pattern"""
        mock_processor = Mock()
        mock_processor.find_audio_files.return_value = [Path("test.mp3")]
        mock_processor.process_files.return_value = [Mock(success=True)]
        mock_processor.skipped_count = 0
        mock_batch_processor_class.return_value = mock_processor
        
        with tempfile.TemporaryDirectory() as input_dir:
            result = self.runner.invoke(app, [
                "batch",
                input_dir,
                "--pattern", "*.mp3",
                "--output-dir", str(temp_output_dir),
                "--algorithm", "librosa"
            ])
        
        assert result.exit_code == 0
        mock_processor.find_audio_files.assert_called_once_with(
            Path(input_dir), pattern="*.mp3", recursive=False
        )
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor')
    def test_batch_recursive(self, mock_batch_processor_class, temp_output_dir):
        """Test batch command with recursive option"""
        mock_processor = Mock()
        mock_processor.find_audio_files.return_value = []
        mock_processor.process_files.return_value = []
        mock_processor.skipped_count = 0
        mock_batch_processor_class.return_value = mock_processor
        
        with tempfile.TemporaryDirectory() as input_dir:
            result = self.runner.invoke(app, [
                "batch",
                input_dir,
                "--recursive",
                "--output-dir", str(temp_output_dir),
                "--algorithm", "librosa"
            ])
        
        assert result.exit_code == 0
        mock_processor.find_audio_files.assert_called_once_with(
            Path(input_dir), pattern="*", recursive=True
        )
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor')
    def test_batch_no_files_found(self, mock_batch_processor_class, temp_output_dir):
        """Test batch command when no files are found"""
        mock_processor = Mock()
        mock_processor.find_audio_files.return_value = []
        mock_batch_processor_class.return_value = mock_processor
        
        with tempfile.TemporaryDirectory() as input_dir:
            result = self.runner.invoke(app, [
                "batch",
                input_dir,
                "--output-dir", str(temp_output_dir),
                "--algorithm", "librosa"
            ])
        
        assert result.exit_code == 0
        assert "No audio files found" in result.stdout
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor')
    def test_batch_with_failures(self, mock_batch_processor_class, temp_output_dir):
        """Test batch command with some failures"""
        mock_processor = Mock()
        mock_processor.find_audio_files.return_value = [Path("test1.mp3"), Path("test2.mp3")]
        mock_processor.process_files.return_value = [
            Mock(success=True),
            Mock(success=False)
        ]
        mock_processor.skipped_count = 0
        mock_batch_processor_class.return_value = mock_processor
        
        with tempfile.TemporaryDirectory() as input_dir:
            result = self.runner.invoke(app, [
                "batch",
                input_dir,
                "--output-dir", str(temp_output_dir),
                "--algorithm", "librosa"
            ])
        
        assert result.exit_code == 0
        assert "Successful" in result.stdout
        assert "Failed" in result.stdout
        assert "1" in result.stdout  # 1 success, 1 failure
    
    @patch('bpm_analyzer.processors.batch.BatchProcessor')
    def test_batch_error_handling(self, mock_batch_processor_class, temp_output_dir):
        """Test batch command error handling"""
        mock_processor = Mock()
        mock_processor.find_audio_files.side_effect = Exception("Batch processing failed")
        mock_batch_processor_class.return_value = mock_processor
        
        with tempfile.TemporaryDirectory() as input_dir:
            result = self.runner.invoke(app, [
                "batch",
                input_dir,
                "--output-dir", str(temp_output_dir),
                "--algorithm", "librosa"
            ])
        
        assert result.exit_code == 1
        assert "Batch processing error" in result.stdout


class TestDbCommand:
    """Test database command"""
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    @patch('bpm_analyzer.db.database.AnalysisDB')
    def test_db_init(self, mock_db_class):
        """Test database init command"""
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        result = self.runner.invoke(app, [
            "db", "init",
            "--database", "sqlite:///test.db"
        ])
        
        assert result.exit_code == 0
        assert "Database initialized" in result.stdout
        
        mock_db_class.assert_called_once_with("sqlite:///test.db")
        mock_db.init_db.assert_called_once()
    
    @patch('bpm_analyzer.db.database.AnalysisDB')
    def test_db_query(self, mock_db_class):
        """Test database query command"""
        mock_db = Mock()
        mock_analysis = Mock()
        mock_analysis.average_bpm = 120.0
        mock_analysis.beat_count = 100
        mock_analysis.audio_file.file_path = "/test/file.mp3"
        mock_analysis.audio_file.duration = 180.0
        mock_db.query_tempo_range.return_value = [mock_analysis]
        mock_db_class.return_value = mock_db
        
        result = self.runner.invoke(app, [
            "db", "query",
            "--min-bpm", "100",
            "--max-bpm", "140"
        ])
        
        assert result.exit_code == 0
        assert "file.mp3" in result.stdout
        assert "120.0" in result.stdout
        
        mock_db.query_tempo_range.assert_called_once_with(
            min_bpm=100.0, max_bpm=140.0
        )
    
    @patch('bpm_analyzer.db.database.AnalysisDB')
    def test_db_stats(self, mock_db_class):
        """Test database stats command"""
        mock_db = Mock()
        mock_db.get_statistics.return_value = {
            "total_files": 10,
            "total_analyses": 15,
            "avg_bpm": 120.5,
            "min_bpm": 80.0,
            "max_bpm": 180.0
        }
        mock_db_class.return_value = mock_db
        
        result = self.runner.invoke(app, [
            "db", "stats"
        ])
        
        assert result.exit_code == 0
        assert "Database Statistics" in result.stdout
        assert "10" in result.stdout  # total files
        assert "120.5" in result.stdout  # avg bpm
        
        mock_db.get_statistics.assert_called_once()
    
    @patch('bpm_analyzer.db.database.AnalysisDB')
    def test_db_export(self, mock_db_class, temp_output_dir):
        """Test database export command"""
        mock_db = Mock()
        mock_db.export_to_csv.return_value = 25
        mock_db_class.return_value = mock_db
        
        output_file = temp_output_dir / "export.csv"
        
        result = self.runner.invoke(app, [
            "db", "export",
            "--output", str(output_file)
        ])
        
        assert result.exit_code == 0
        assert "Exported 25 entries" in result.stdout
        
        mock_db.export_to_csv.assert_called_once_with(output_file)
    
    def test_db_invalid_action(self):
        """Test database command with invalid action"""
        result = self.runner.invoke(app, [
            "db", "invalid_action"
        ])
        
        assert result.exit_code == 1
        assert "Unknown action" in result.stdout


class TestValidateCommand:
    """Test validate command"""
    
    def setup_method(self):
        """Setup test runner"""
        self.runner = CliRunner()
    
    @patch('bpm_analyzer.utils.validation.validate_audio_file')
    def test_validate_success(self, mock_validate, temp_audio_file):
        """Test validate command with valid file"""
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.format = "wav"
        mock_result.duration = 5.0
        mock_result.sample_rate = 44100
        mock_result.channels = 1
        mock_validate.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "validate",
            str(temp_audio_file)
        ])
        
        assert result.exit_code == 0
        assert "Audio file is valid" in result.stdout
        assert "wav" in result.stdout
        assert "5.0s" in result.stdout
        assert "44100Hz" in result.stdout
    
    @patch('bpm_analyzer.utils.validation.validate_audio_file')
    def test_validate_failure(self, mock_validate, temp_audio_file):
        """Test validate command with invalid file"""
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.error = "Invalid audio format"
        mock_validate.return_value = mock_result
        
        result = self.runner.invoke(app, [
            "validate",
            str(temp_audio_file)
        ])
        
        assert result.exit_code == 0
        assert "Audio file validation failed" in result.stdout
        assert "Invalid audio format" in result.stdout
    
    @patch('bpm_analyzer.utils.validation.validate_audio_file')
    def test_validate_error_handling(self, mock_validate, temp_audio_file):
        """Test validate command error handling"""
        mock_validate.side_effect = Exception("Validation error")
        
        result = self.runner.invoke(app, [
            "validate",
            str(temp_audio_file)
        ])
        
        assert result.exit_code == 1
        assert "Validation error" in result.stdout


class TestEnums:
    """Test CLI enums"""
    
    def test_algorithm_enum(self):
        """Test Algorithm enum values"""
        assert Algorithm.madmom.value == "madmom"
        assert Algorithm.essentia.value == "essentia"
        assert Algorithm.librosa.value == "librosa"
        assert Algorithm.aubio.value == "aubio"
        assert Algorithm.ensemble.value == "ensemble"
    
    def test_output_format_enum(self):
        """Test OutputFormat enum values"""
        assert OutputFormat.jams.value == "jams"
        assert OutputFormat.csv.value == "csv"
        assert OutputFormat.json.value == "json"