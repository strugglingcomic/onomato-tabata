import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bpm_analyzer.db.database import AnalysisDB
from bpm_analyzer.db.models import Base, AudioFile, Analysis, Beat, TempoPoint
from bpm_analyzer.core.analyzer import AnalysisResult
from bpm_analyzer.core.tempo_map import Beat as BeatData
import numpy as np


class TestAnalysisDB:
    """Test AnalysisDB class"""
    
    def test_init_default(self):
        """Test AnalysisDB initialization with default URL"""
        db = AnalysisDB()
        assert "sqlite:///music_tempo.db" in db.database_url
        assert db.engine is not None
        assert db.SessionLocal is not None
    
    def test_init_custom_url(self):
        """Test AnalysisDB initialization with custom URL"""
        custom_url = "sqlite:///custom.db"
        db = AnalysisDB(custom_url)
        assert db.database_url == custom_url
    
    def test_init_db(self, temp_db):
        """Test database initialization"""
        # temp_db fixture already calls init_db
        assert temp_db.engine is not None
        
        # Check that tables exist
        from sqlalchemy import inspect
        inspector = inspect(temp_db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['audio_files', 'analyses', 'beats', 'tempo_points', 'tags', 'audio_file_tags']
        for table in expected_tables:
            assert table in tables
    
    def test_get_session(self, temp_db):
        """Test getting database session"""
        session = temp_db.get_session()
        assert session is not None
        session.close()
    
    def test_store_analysis_new_file(self, temp_db, temp_audio_file):
        """Test storing analysis result with new audio file"""
        # Create test data
        beats = [
            BeatData(time=0.5, position=1, confidence=0.9),
            BeatData(time=1.0, position=2, confidence=0.8)
        ]
        
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=beats,
            algorithm="librosa",
            processing_time=1.5,
            warnings=["test warning"]
        )
        
        # Store analysis
        analysis_id = temp_db.store_analysis(result)
        
        assert analysis_id is not None
        assert analysis_id > 0
        
        # Verify stored data
        with temp_db.get_session() as session:
            analysis = session.query(Analysis).get(analysis_id)
            assert analysis is not None
            assert analysis.algorithm == "librosa"
            assert analysis.average_bpm == 120.0
            assert analysis.beat_count == 2
            assert analysis.processing_time == 1.5
            assert "test warning" in analysis.warnings
            
            # Check audio file
            audio_file = analysis.audio_file
            assert audio_file is not None
            assert audio_file.file_path == str(temp_audio_file)
            assert audio_file.duration == 5.0
            assert audio_file.sample_rate == 44100
            
            # Check beats
            stored_beats = session.query(Beat).filter_by(analysis_id=analysis_id).all()
            assert len(stored_beats) == 2
            assert stored_beats[0].time == 0.5
            assert stored_beats[0].position == 1
            assert stored_beats[0].confidence == 0.9
    
    def test_store_analysis_existing_file(self, temp_db, temp_audio_file):
        """Test storing analysis for existing audio file"""
        # Store first analysis
        beats = [BeatData(time=0.5, position=1, confidence=0.9)]
        result1 = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=beats,
            algorithm="librosa",
            processing_time=1.5
        )
        
        analysis_id1 = temp_db.store_analysis(result1)
        
        # Store second analysis with different algorithm
        result2 = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=125.0,
            beats=beats,
            algorithm="madmom",
            processing_time=2.0
        )
        
        analysis_id2 = temp_db.store_analysis(result2)
        
        assert analysis_id1 != analysis_id2
        
        # Verify both analyses exist for same file
        with temp_db.get_session() as session:
            audio_files = session.query(AudioFile).all()
            assert len(audio_files) == 1  # Only one audio file
            
            analyses = session.query(Analysis).all()
            assert len(analyses) == 2  # Two analyses
    
    def test_store_analysis_duplicate(self, temp_db, temp_audio_file):
        """Test storing duplicate analysis (same file + algorithm)"""
        beats = [BeatData(time=0.5, position=1, confidence=0.9)]
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=beats,
            algorithm="librosa",
            processing_time=1.5
        )
        
        # Store first time
        analysis_id1 = temp_db.store_analysis(result)
        
        # Try to store duplicate
        analysis_id2 = temp_db.store_analysis(result)
        
        # Should return same analysis ID
        assert analysis_id1 == analysis_id2
        
        # Verify only one analysis exists
        with temp_db.get_session() as session:
            analyses = session.query(Analysis).all()
            assert len(analyses) == 1
    
    def test_store_analysis_with_tempo_curve(self, temp_db, temp_audio_file):
        """Test storing analysis with tempo curve"""
        beats = [BeatData(time=0.5, position=1, confidence=0.9)]
        tempo_curve = np.array([120.0, 121.0, 119.0])
        tempo_confidence = np.array([0.9, 0.8, 0.85])
        
        result = AnalysisResult(
            file_path=temp_audio_file,
            duration=5.0,
            sample_rate=44100,
            average_bpm=120.0,
            beats=beats,
            algorithm="librosa",
            processing_time=1.5,
            tempo_curve=tempo_curve,
            tempo_confidence=tempo_confidence
        )
        
        analysis_id = temp_db.store_analysis(result)
        
        # Verify tempo points were stored
        with temp_db.get_session() as session:
            tempo_points = session.query(TempoPoint).filter_by(analysis_id=analysis_id).all()
            assert len(tempo_points) == 3
            assert tempo_points[0].bpm == 120.0
            assert tempo_points[1].bpm == 121.0
            assert tempo_points[2].bpm == 119.0
    
    def test_query_tempo_range_basic(self, temp_db):
        """Test basic tempo range query"""
        # Add test data
        with temp_db.get_session() as session:
            audio_file = AudioFile(
                file_path="/test/file.mp3",
                file_hash="test_hash",
                duration=180.0,
                sample_rate=44100,
                channels=2,
                format="mp3",
                file_size=1024
            )
            session.add(audio_file)
            session.flush()
            
            analysis1 = Analysis(
                audio_file_id=audio_file.id,
                algorithm="librosa",
                average_bpm=100.0,
                beat_count=200,
                processing_time=1.0
            )
            
            analysis2 = Analysis(
                audio_file_id=audio_file.id,
                algorithm="madmom",
                average_bpm=150.0,
                beat_count=300,
                processing_time=2.0
            )
            
            session.add(analysis1)
            session.add(analysis2)
            session.commit()
        
        # Query tempo range
        results = temp_db.query_tempo_range(min_bpm=90, max_bpm=120)
        
        assert len(results) == 1
        assert results[0].average_bpm == 100.0
        assert results[0].algorithm == "librosa"
    
    def test_query_tempo_range_no_limits(self, temp_db):
        """Test tempo range query without limits"""
        # Add test data
        with temp_db.get_session() as session:
            audio_file = AudioFile(
                file_path="/test/file.mp3",
                file_hash="test_hash",
                duration=180.0,
                sample_rate=44100,
                channels=2,
                format="mp3",
                file_size=1024
            )
            session.add(audio_file)
            session.flush()
            
            analysis = Analysis(
                audio_file_id=audio_file.id,
                algorithm="librosa",
                average_bpm=120.0,
                beat_count=200,
                processing_time=1.0
            )
            session.add(analysis)
            session.commit()
        
        # Query without limits
        results = temp_db.query_tempo_range()
        
        assert len(results) == 1
        assert results[0].average_bpm == 120.0
    
    def test_query_tempo_range_with_algorithm(self, temp_db):
        """Test tempo range query with algorithm filter"""
        # Add test data
        with temp_db.get_session() as session:
            audio_file = AudioFile(
                file_path="/test/file.mp3",
                file_hash="test_hash",
                duration=180.0,
                sample_rate=44100,
                channels=2,
                format="mp3",
                file_size=1024
            )
            session.add(audio_file)
            session.flush()
            
            analysis1 = Analysis(
                audio_file_id=audio_file.id,
                algorithm="librosa",
                average_bpm=120.0,
                beat_count=200,
                processing_time=1.0
            )
            
            analysis2 = Analysis(
                audio_file_id=audio_file.id,
                algorithm="madmom",
                average_bpm=120.0,
                beat_count=200,
                processing_time=2.0
            )
            
            session.add(analysis1)
            session.add(analysis2)
            session.commit()
        
        # Query with algorithm filter
        results = temp_db.query_tempo_range(algorithm="librosa")
        
        assert len(results) == 1
        assert results[0].algorithm == "librosa"
    
    def test_query_tempo_range_with_limit(self, temp_db):
        """Test tempo range query with result limit"""
        # Add test data
        with temp_db.get_session() as session:
            audio_file = AudioFile(
                file_path="/test/file.mp3",
                file_hash="test_hash",
                duration=180.0,
                sample_rate=44100,
                channels=2,
                format="mp3",
                file_size=1024
            )
            session.add(audio_file)
            session.flush()
            
            for i in range(5):
                analysis = Analysis(
                    audio_file_id=audio_file.id,
                    algorithm=f"algo{i}",
                    average_bpm=120.0 + i,
                    beat_count=200,
                    processing_time=1.0
                )
                session.add(analysis)
            
            session.commit()
        
        # Query with limit
        results = temp_db.query_tempo_range(limit=3)
        
        assert len(results) == 3
        # Should be ordered by BPM
        assert results[0].average_bpm <= results[1].average_bpm <= results[2].average_bpm
    
    def test_get_statistics(self, temp_db):
        """Test getting database statistics"""
        # Add test data
        with temp_db.get_session() as session:
            audio_file = AudioFile(
                file_path="/test/file.mp3",
                file_hash="test_hash",
                duration=180.0,
                sample_rate=44100,
                channels=2,
                format="mp3",
                file_size=1024
            )
            session.add(audio_file)
            session.flush()
            
            analysis = Analysis(
                audio_file_id=audio_file.id,
                algorithm="librosa",
                average_bpm=120.0,
                beat_count=200,
                processing_time=1.0
            )
            session.add(analysis)
            session.flush()
            
            beat = Beat(
                analysis_id=analysis.id,
                time=0.5,
                position=1,
                confidence=0.9
            )
            session.add(beat)
            session.commit()
        
        # Get statistics
        stats = temp_db.get_statistics()
        
        assert stats["total_files"] == 1
        assert stats["total_analyses"] == 1
        assert stats["total_beats"] == 1
        assert stats["avg_bpm"] == 120.0
        assert stats["min_bpm"] == 120.0
        assert stats["max_bpm"] == 120.0
        assert stats["total_duration"] == 180.0
        assert "by_algorithm" in stats
        assert "librosa" in stats["by_algorithm"]
    
    def test_export_to_csv(self, temp_db, temp_output_dir):
        """Test exporting database to CSV"""
        # Add test data
        with temp_db.get_session() as session:
            audio_file = AudioFile(
                file_path="/test/file.mp3",
                file_hash="test_hash",
                duration=180.0,
                sample_rate=44100,
                channels=2,
                format="mp3",
                file_size=1024
            )
            session.add(audio_file)
            session.flush()
            
            analysis = Analysis(
                audio_file_id=audio_file.id,
                algorithm="librosa",
                average_bpm=120.0,
                beat_count=200,
                processing_time=1.0,
                confidence=0.9
            )
            session.add(analysis)
            session.commit()
        
        # Export to CSV
        output_file = temp_output_dir / "export.csv"
        count = temp_db.export_to_csv(output_file)
        
        assert count == 1
        assert output_file.exists()
        
        # Verify CSV content
        import csv
        with open(output_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            expected_header = ['file_path', 'algorithm', 'average_bpm', 'beat_count', 'duration', 'confidence']
            assert header == expected_header
            
            row = next(reader)
            assert row[0] == "/test/file.mp3"
            assert row[1] == "librosa"
            assert float(row[2]) == 120.0
            assert int(row[3]) == 200
            assert float(row[4]) == 180.0
            assert float(row[5]) == 0.9
    
    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_calculate_file_hash_error(self, mock_open, temp_db):
        """Test file hash calculation with file error"""
        with pytest.raises(IOError):
            temp_db._calculate_file_hash(Path("/nonexistent/file.mp3"))
    
    def test_calculate_file_hash_success(self, temp_db, temp_audio_file):
        """Test successful file hash calculation"""
        hash_value = temp_db._calculate_file_hash(temp_audio_file)
        
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex string
        assert isinstance(hash_value, str)
        
        # Hash should be consistent
        hash_value2 = temp_db._calculate_file_hash(temp_audio_file)
        assert hash_value == hash_value2


class TestDatabaseModels:
    """Test database models"""
    
    def test_audio_file_model(self):
        """Test AudioFile model"""
        audio_file = AudioFile(
            file_path="/test/file.mp3",
            file_hash="test_hash",
            duration=180.0,
            sample_rate=44100,
            channels=2,
            format="mp3",
            file_size=1024
        )
        
        assert audio_file.file_path == "/test/file.mp3"
        assert audio_file.file_hash == "test_hash"
        assert audio_file.duration == 180.0
        assert audio_file.sample_rate == 44100
        assert audio_file.channels == 2
        assert audio_file.format == "mp3"
        assert audio_file.file_size == 1024
        assert audio_file.created_at is not None
    
    def test_analysis_model(self):
        """Test Analysis model"""
        analysis = Analysis(
            audio_file_id=1,
            algorithm="librosa",
            average_bpm=120.0,
            beat_count=200,
            processing_time=1.5,
            confidence=0.9
        )
        
        assert analysis.audio_file_id == 1
        assert analysis.algorithm == "librosa"
        assert analysis.average_bpm == 120.0
        assert analysis.beat_count == 200
        assert analysis.processing_time == 1.5
        assert analysis.confidence == 0.9
        assert analysis.created_at is not None
    
    def test_beat_model(self):
        """Test Beat model"""
        beat = Beat(
            analysis_id=1,
            time=0.5,
            position=1,
            confidence=0.9,
            is_downbeat=1
        )
        
        assert beat.analysis_id == 1
        assert beat.time == 0.5
        assert beat.position == 1
        assert beat.confidence == 0.9
        assert beat.is_downbeat == 1
    
    def test_tempo_point_model(self):
        """Test TempoPoint model"""
        tempo_point = TempoPoint(
            analysis_id=1,
            time=0.5,
            bpm=120.0,
            confidence=0.9
        )
        
        assert tempo_point.analysis_id == 1
        assert tempo_point.time == 0.5
        assert tempo_point.bpm == 120.0
        assert tempo_point.confidence == 0.9