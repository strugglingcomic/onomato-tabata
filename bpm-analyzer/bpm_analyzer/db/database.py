"""
Database interface for BPM Analyzer
"""
import hashlib
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import create_engine, select, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from bpm_analyzer.db.models import Base, AudioFile, Analysis, Beat, TempoPoint
from bpm_analyzer.core.analyzer import AnalysisResult
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class AnalysisDB:
    """Database interface for storing and querying analysis results"""
    
    def __init__(self, database_url: str = "sqlite:///music_tempo.db"):
        """
        Initialize database connection.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self) -> None:
        """Initialize database schema"""
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {self.database_url}")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def store_analysis(self, result: AnalysisResult) -> int:
        """
        Store analysis result in database.
        
        Args:
            result: Analysis result to store
            
        Returns:
            Analysis ID
        """
        with self.get_session() as session:
            # Get or create audio file
            file_hash = self._calculate_file_hash(result.file_path)
            audio_file = session.query(AudioFile).filter_by(
                file_path=str(result.file_path)
            ).first()
            
            if not audio_file:
                audio_file = AudioFile(
                    file_path=str(result.file_path),
                    file_hash=file_hash,
                    duration=result.duration,
                    sample_rate=result.sample_rate,
                    channels=1,  # TODO: Get from audio loader
                    format=result.file_path.suffix[1:],
                    file_size=result.file_path.stat().st_size,
                )
                session.add(audio_file)
                session.flush()
            
            # Check if analysis already exists
            existing = session.query(Analysis).filter_by(
                audio_file_id=audio_file.id,
                algorithm=result.algorithm
            ).first()
            
            if existing:
                logger.warning(
                    f"Analysis already exists for {result.file_path} "
                    f"with {result.algorithm}"
                )
                return existing.id
            
            # Create analysis
            analysis = Analysis(
                audio_file_id=audio_file.id,
                algorithm=result.algorithm,
                average_bpm=result.average_bpm,
                beat_count=len(result.beats),
                processing_time=result.processing_time,
                warnings=json.dumps(result.warnings) if result.warnings else None,
            )
            session.add(analysis)
            session.flush()
            
            # Add beats
            for beat in result.beats:
                beat_obj = Beat(
                    analysis_id=analysis.id,
                    time=beat.time,
                    position=beat.position,
                    confidence=beat.confidence,
                    is_downbeat=1 if beat.position == 1 else 0,
                )
                session.add(beat_obj)
            
            # Add tempo points if available
            if result.tempo_curve is not None:
                for i, (bpm, conf) in enumerate(
                    zip(result.tempo_curve, result.tempo_confidence)
                ):
                    tempo_point = TempoPoint(
                        analysis_id=analysis.id,
                        time=i * 0.1,  # Assuming 10Hz
                        bpm=float(bpm),
                        confidence=float(conf),
                    )
                    session.add(tempo_point)
            
            session.commit()
            logger.info(f"Stored analysis {analysis.id} for {result.file_path}")
            return analysis.id
    
    def query_tempo_range(
        self,
        min_bpm: Optional[float] = None,
        max_bpm: Optional[float] = None,
        algorithm: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Analysis]:
        """
        Query analyses by tempo range.
        
        Args:
            min_bpm: Minimum BPM (inclusive)
            max_bpm: Maximum BPM (inclusive)
            algorithm: Filter by algorithm
            limit: Maximum number of results
            
        Returns:
            List of Analysis objects
        """
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            query = session.query(Analysis).options(joinedload(Analysis.audio_file))
            
            if min_bpm is not None:
                query = query.filter(Analysis.average_bpm >= min_bpm)
            if max_bpm is not None:
                query = query.filter(Analysis.average_bpm <= max_bpm)
            if algorithm:
                query = query.filter(Analysis.algorithm == algorithm)
            
            query = query.order_by(Analysis.average_bpm)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_session() as session:
            stats = {
                "total_files": session.query(func.count(AudioFile.id)).scalar(),
                "total_analyses": session.query(func.count(Analysis.id)).scalar(),
                "total_beats": session.query(func.count(Beat.id)).scalar(),
                "avg_bpm": session.query(func.avg(Analysis.average_bpm)).scalar(),
                "min_bpm": session.query(func.min(Analysis.average_bpm)).scalar(),
                "max_bpm": session.query(func.max(Analysis.average_bpm)).scalar(),
                "total_duration": session.query(func.sum(AudioFile.duration)).scalar(),
            }
            
            # Algorithm breakdown
            algo_stats = session.query(
                Analysis.algorithm,
                func.count(Analysis.id).label("count"),
                func.avg(Analysis.average_bpm).label("avg_bpm")
            ).group_by(Analysis.algorithm).all()
            
            stats["by_algorithm"] = {
                algo: {"count": count, "avg_bpm": avg_bpm}
                for algo, count, avg_bpm in algo_stats
            }
            
            return stats
    
    def export_to_csv(self, output_path: Path) -> int:
        """
        Export database to CSV.
        
        Args:
            output_path: Path for CSV file
            
        Returns:
            Number of records exported
        """
        import csv
        
        with self.get_session() as session:
            analyses = session.query(Analysis).all()
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'file_path', 'algorithm', 'average_bpm', 
                    'beat_count', 'duration', 'confidence'
                ])
                
                count = 0
                for analysis in analyses:
                    writer.writerow([
                        analysis.audio_file.file_path,
                        analysis.algorithm,
                        analysis.average_bpm,
                        analysis.beat_count,
                        analysis.audio_file.duration,
                        analysis.confidence,
                    ])
                    count += 1
            
            return count
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
