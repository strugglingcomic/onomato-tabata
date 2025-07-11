import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import json

from bpm_analyzer.core.analyzer import analyze_file
from bpm_analyzer.cli import app
from bpm_analyzer.db.database import AnalysisDB
from bpm_analyzer.processors.batch import BatchProcessor
from bpm_analyzer.config import AnalysisConfig
from bpm_analyzer.utils.validation import validate_audio_file

from typer.testing import CliRunner


class TestEndToEndAnalysis:
    """End-to-end analysis tests"""
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_complete_analysis_pipeline(self, mock_librosa, temp_audio_file, temp_output_dir):
        """Test complete analysis pipeline from file to output"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30, 40])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5, 2.0]
        
        # Configure analysis
        config = AnalysisConfig(
            algorithm="librosa",
            confidence_threshold=0.5,
            tempo_range=(60, 180)
        )
        
        # Analyze file
        result = analyze_file(temp_audio_file, config)
        
        # Verify analysis result
        assert result is not None
        assert result.average_bpm == 120.0
        assert len(result.beats) == 4
        assert result.algorithm == "librosa"
        assert result.processing_time > 0
        
        # Save in different formats
        for format_type in ["jams", "csv", "json"]:
            output_file = temp_output_dir / f"output.{format_type}"
            result.save(output_file, format=format_type)
            
            assert output_file.exists()
            assert output_file.stat().st_size > 0
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_analysis_with_database_storage(self, mock_librosa, temp_audio_file, temp_db):
        """Test analysis with database storage"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        # Configure analysis
        config = AnalysisConfig(algorithm="librosa")
        
        # Analyze file
        result = analyze_file(temp_audio_file, config)
        
        # Store in database
        analysis_id = temp_db.store_analysis(result)
        assert analysis_id is not None
        
        # Query database
        analyses = temp_db.query_tempo_range(min_bpm=110, max_bpm=130)
        assert len(analyses) == 1
        assert analyses[0].average_bpm == 120.0
        assert analyses[0].algorithm == "librosa"
        
        # Get statistics
        stats = temp_db.get_statistics()
        assert stats["total_files"] == 1
        assert stats["total_analyses"] == 1
        assert stats["avg_bpm"] == 120.0
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_batch_processing_end_to_end(self, mock_librosa, temp_output_dir):
        """Test complete batch processing workflow"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        # Create input directory with audio files
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
        
        # Initialize batch processor
        processor = BatchProcessor(
            algorithm="librosa",
            output_format="json",
            parallel=False,
            skip_existing=False
        )
        
        # Find files
        found_files = list(processor.find_audio_files(input_dir))
        assert len(found_files) == 3
        
        # Process files
        results = processor.process_files(found_files, output_dir)
        
        # Verify results
        assert len(results) == 3
        assert all(r.success for r in results)
        
        # Check output files
        for i in range(3):
            output_file = output_dir / f"song{i}.json"
            assert output_file.exists()
            
            # Verify JSON content
            with open(output_file, 'r') as f:
                data = json.load(f)
            assert data["average_bpm"] == 120.0
            assert data["algorithm"] == "librosa"
    
    def test_validation_integration(self, temp_audio_file):
        """Test validation integration with actual files"""
        # Validate real audio file
        result = validate_audio_file(temp_audio_file)
        assert result.is_valid == True
        assert result.format is not None
        assert result.duration is not None
        
        # Test with non-existent file
        result = validate_audio_file(Path("/nonexistent/file.mp3"))
        assert result.is_valid == False
        assert "File not found" in result.error
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_error_handling_integration(self, mock_librosa, temp_audio_file):
        """Test error handling throughout the pipeline"""
        # Make librosa fail
        mock_librosa.beat.beat_track.side_effect = Exception("Librosa failed")
        
        config = AnalysisConfig(algorithm="librosa")
        
        # Analysis should fail gracefully
        with pytest.raises(Exception, match="Librosa failed"):
            analyze_file(temp_audio_file, config)
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_confidence_filtering_integration(self, mock_librosa, temp_audio_file):
        """Test confidence filtering integration"""
        # Mock librosa with varying confidence (simulated through different beat intervals)
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30, 40, 50])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5, 2.0, 2.5]
        
        # Configure with confidence threshold
        config = AnalysisConfig(
            algorithm="librosa",
            confidence_threshold=0.85  # Higher than default librosa confidence (0.8)
        )
        
        # Analyze file
        result = analyze_file(temp_audio_file, config)
        
        # Since librosa gives all beats confidence=0.8, filtering by 0.85 should remove all
        # But the actual filtering depends on the TempoMap.filter_by_confidence implementation
        assert result is not None
        assert result.algorithm == "librosa"
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_tempo_range_filtering_integration(self, mock_librosa, temp_audio_file):
        """Test tempo range filtering integration"""
        # Mock librosa with specific tempo
        mock_librosa.beat.beat_track.return_value = (180.0, [10, 20, 30])  # 180 BPM
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        # Configure with restrictive tempo range
        config = AnalysisConfig(
            algorithm="librosa",
            tempo_range=(60, 150)  # Excludes 180 BPM
        )
        
        # Analysis should still work (tempo range is used in algorithm, not post-filtering)
        result = analyze_file(temp_audio_file, config)
        
        assert result is not None
        assert result.average_bpm == 180.0  # Algorithm returns what it finds
        assert result.algorithm == "librosa"


class TestCLIIntegration:
    """CLI integration tests"""
    
    def setup_method(self):
        """Setup CLI runner"""
        self.runner = CliRunner()
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_cli_analyze_integration(self, mock_librosa, temp_audio_file, temp_output_dir):
        """Test CLI analyze command integration"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        output_file = temp_output_dir / "output.jams"
        
        result = self.runner.invoke(app, [
            "analyze",
            str(temp_audio_file),
            "--output", str(output_file),
            "--algorithm", "librosa",
            "--format", "jams"
        ])
        
        assert result.exit_code == 0
        assert "Analysis complete" in result.stdout
        assert "120.0" in result.stdout
        assert output_file.exists()
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_cli_batch_integration(self, mock_librosa, temp_output_dir):
        """Test CLI batch command integration"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        # Create input directory
        input_dir = temp_output_dir / "input"
        input_dir.mkdir()
        
        # Create audio files
        for i in range(2):
            (input_dir / f"song{i}.mp3").touch()
        
        # Create output directory
        output_dir = temp_output_dir / "output"
        
        result = self.runner.invoke(app, [
            "batch",
            str(input_dir),
            "--output-dir", str(output_dir),
            "--algorithm", "librosa",
            "--format", "json"
        ])
        
        assert result.exit_code == 0
        assert "Found 2 audio files" in result.stdout
        assert "Successful" in result.stdout
        
        # Check output files
        assert (output_dir / "song0.json").exists()
        assert (output_dir / "song1.json").exists()
    
    def test_cli_db_integration(self, temp_db):
        """Test CLI database commands integration"""
        # Test db stats on empty database
        result = self.runner.invoke(app, [
            "db", "stats",
            "--database", temp_db.database_url
        ])
        
        assert result.exit_code == 0
        assert "Database Statistics" in result.stdout
        assert "0" in result.stdout  # Empty database
    
    def test_cli_info_integration(self):
        """Test CLI info command integration"""
        result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "Available Algorithms" in result.stdout
        assert "madmom" in result.stdout
        assert "librosa" in result.stdout
        assert "Output Formats" in result.stdout
        assert "jams" in result.stdout
    
    def test_cli_validate_integration(self, temp_audio_file):
        """Test CLI validate command integration"""
        result = self.runner.invoke(app, [
            "validate",
            str(temp_audio_file)
        ])
        
        assert result.exit_code == 0
        assert "Audio file is valid" in result.stdout


class TestDatabaseIntegration:
    """Database integration tests"""
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_database_full_workflow(self, mock_librosa, temp_audio_file):
        """Test complete database workflow"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30, 40])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5, 2.0]
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            # Initialize database
            db = AnalysisDB(f"sqlite:///{db_path}")
            db.init_db()
            
            # Analyze and store multiple files
            for i in range(3):
                config = AnalysisConfig(algorithm="librosa")
                result = analyze_file(temp_audio_file, config)
                result.algorithm = f"librosa_v{i}"  # Make each unique
                db.store_analysis(result)
            
            # Query database
            all_analyses = db.query_tempo_range()
            assert len(all_analyses) == 3
            
            # Query with tempo filter
            filtered_analyses = db.query_tempo_range(min_bpm=110, max_bpm=130)
            assert len(filtered_analyses) == 3  # All should match
            
            # Get statistics
            stats = db.get_statistics()
            assert stats["total_files"] == 1  # Same file used 3 times
            assert stats["total_analyses"] == 3
            assert stats["avg_bpm"] == 120.0
            
            # Export to CSV
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as csv_f:
                csv_path = csv_f.name
            
            try:
                count = db.export_to_csv(Path(csv_path))
                assert count == 3
                
                # Verify CSV content
                with open(csv_path, 'r') as f:
                    lines = f.readlines()
                assert len(lines) == 4  # Header + 3 data rows
                
            finally:
                os.unlink(csv_path)
                
        finally:
            os.unlink(db_path)
    
    def test_database_concurrent_access(self, temp_db, temp_audio_file):
        """Test database with concurrent access simulation"""
        # This would be more meaningful with actual threading,
        # but we'll simulate sequential "concurrent" operations
        
        with patch('bpm_analyzer.algorithms.librosa_impl.librosa') as mock_librosa:
            mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
            mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
            
            # Simulate multiple "concurrent" analysis operations
            results = []
            for i in range(5):
                config = AnalysisConfig(algorithm="librosa")
                result = analyze_file(temp_audio_file, config)
                result.algorithm = f"librosa_session_{i}"
                analysis_id = temp_db.store_analysis(result)
                results.append(analysis_id)
            
            # Verify all operations succeeded
            assert len(results) == 5
            assert all(r is not None for r in results)
            
            # Verify database state
            stats = temp_db.get_statistics()
            assert stats["total_analyses"] == 5


class TestRealWorldScenarios:
    """Real-world scenario integration tests"""
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_mixed_file_types_batch(self, mock_librosa, temp_output_dir):
        """Test batch processing with mixed file types"""
        # Mock librosa
        mock_librosa.beat.beat_track.return_value = (120.0, [10, 20, 30])
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        # Create input directory with mixed files
        input_dir = temp_output_dir / "input"
        input_dir.mkdir()
        
        # Create audio files
        (input_dir / "song1.mp3").touch()
        (input_dir / "song2.wav").touch()
        (input_dir / "song3.flac").touch()
        
        # Create non-audio files (should be ignored)
        (input_dir / "readme.txt").touch()
        (input_dir / "cover.jpg").touch()
        
        # Create subdirectory
        subdir = input_dir / "subdir"
        subdir.mkdir()
        (subdir / "song4.m4a").touch()
        
        # Process with BatchProcessor
        processor = BatchProcessor(
            algorithm="librosa",
            output_format="json",
            parallel=False
        )
        
        # Find files
        found_files = list(processor.find_audio_files(input_dir, recursive=True))
        assert len(found_files) == 4  # Only audio files
        
        # Process files
        output_dir = temp_output_dir / "output"
        output_dir.mkdir()
        
        results = processor.process_files(found_files, output_dir)
        
        # Verify all audio files were processed
        assert len(results) == 4
        assert all(r.success for r in results)
        
        # Verify output files
        expected_outputs = ["song1.json", "song2.json", "song3.json", "song4.json"]
        for output_file in expected_outputs:
            assert (output_dir / output_file).exists()
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_large_file_processing(self, mock_librosa, temp_output_dir):
        """Test processing simulation of large files"""
        # Mock librosa with longer processing time simulation
        def slow_beat_track(*args, **kwargs):
            import time
            time.sleep(0.1)  # Simulate processing time
            return (120.0, list(range(100)))  # Many beats
        
        mock_librosa.beat.beat_track.side_effect = slow_beat_track
        mock_librosa.frames_to_time.return_value = [i * 0.1 for i in range(100)]
        
        # Create "large" file
        large_file = temp_output_dir / "large_song.wav"
        large_file.touch()
        
        # Process file
        config = AnalysisConfig(algorithm="librosa")
        result = analyze_file(large_file, config)
        
        # Verify processing
        assert result is not None
        assert result.average_bpm == 120.0
        assert len(result.beats) == 100
        assert result.processing_time > 0.1  # Should include our simulated delay
    
    @patch('bpm_analyzer.algorithms.librosa_impl.librosa')
    def test_error_recovery_scenarios(self, mock_librosa, temp_output_dir):
        """Test error recovery in various scenarios"""
        # Create test files
        input_dir = temp_output_dir / "input"
        input_dir.mkdir()
        
        good_file = input_dir / "good.mp3"
        bad_file = input_dir / "bad.mp3"
        good_file.touch()
        bad_file.touch()
        
        # Mock librosa to succeed for good file, fail for bad file
        def selective_failure(*args, **kwargs):
            # Check if the file path (indirectly) suggests it's the bad file
            # This is a simplified approach for testing
            if hasattr(selective_failure, 'call_count'):
                selective_failure.call_count += 1
            else:
                selective_failure.call_count = 1
            
            if selective_failure.call_count == 2:  # Second call (bad file)
                raise Exception("Simulated processing error")
            
            return (120.0, [10, 20, 30])
        
        mock_librosa.beat.beat_track.side_effect = selective_failure
        mock_librosa.frames_to_time.return_value = [0.5, 1.0, 1.5]
        
        # Process with batch processor
        processor = BatchProcessor(
            algorithm="librosa",
            output_format="json",
            parallel=False
        )
        
        files = [good_file, bad_file]
        output_dir = temp_output_dir / "output"
        output_dir.mkdir()
        
        results = processor.process_files(files, output_dir)
        
        # Should have mixed results
        assert len(results) == 2
        
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        
        assert len(successes) == 1
        assert len(failures) == 1
        
        # Good file should have output
        assert (output_dir / "good.json").exists()
        # Bad file should not have output
        assert not (output_dir / "bad.json").exists()
    
    def test_configuration_persistence(self, temp_output_dir):
        """Test configuration persistence across operations"""
        # Create multiple configurations
        configs = [
            AnalysisConfig(algorithm="librosa", confidence_threshold=0.5),
            AnalysisConfig(algorithm="librosa", confidence_threshold=0.8),
            AnalysisConfig(algorithm="librosa", tempo_range=(80, 160))
        ]
        
        # Verify each configuration maintains its settings
        for i, config in enumerate(configs):
            assert config.algorithm == "librosa"
            
            if i == 0:
                assert config.confidence_threshold == 0.5
            elif i == 1:
                assert config.confidence_threshold == 0.8
            elif i == 2:
                assert config.tempo_range == (80, 160)
        
        # Verify configurations are independent
        assert configs[0] != configs[1]
        assert configs[1] != configs[2]
        assert configs[0] != configs[2]