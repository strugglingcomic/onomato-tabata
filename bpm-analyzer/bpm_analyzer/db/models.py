"""
SQLAlchemy database models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    ForeignKey, Index, UniqueConstraint, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AudioFile(Base):
    """Audio file metadata"""
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String(500), unique=True, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA256 hash
    duration = Column(Float, nullable=False)
    sample_rate = Column(Integer, nullable=False)
    channels = Column(Integer, nullable=False)
    format = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="audio_file", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_file_hash", "file_hash"),
    )


class Analysis(Base):
    """Analysis results for an audio file"""
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"), nullable=False)
    algorithm = Column(String(50), nullable=False)
    average_bpm = Column(Float, nullable=False)
    beat_count = Column(Integer, nullable=False)
    confidence = Column(Float, default=1.0)
    processing_time = Column(Float, nullable=False)
    parameters = Column(Text)  # JSON string of analysis parameters
    warnings = Column(Text)  # JSON array of warnings
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    audio_file = relationship("AudioFile", back_populates="analyses")
    beats = relationship("Beat", back_populates="analysis", cascade="all, delete-orphan")
    tempo_points = relationship("TempoPoint", back_populates="analysis", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_analyses_bpm", "average_bpm"),
        Index("idx_analyses_algorithm", "algorithm"),
        UniqueConstraint("audio_file_id", "algorithm", name="uq_file_algorithm"),
    )


class Beat(Base):
    """Individual beat annotations"""
    __tablename__ = "beats"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    time = Column(Float, nullable=False)  # Time in seconds
    position = Column(Integer, nullable=False)  # Beat position in measure
    confidence = Column(Float, default=1.0)
    is_downbeat = Column(Integer, default=0)  # Boolean as integer
    
    # Relationships
    analysis = relationship("Analysis", back_populates="beats")
    
    __table_args__ = (
        Index("idx_beats_time", "analysis_id", "time"),
    )


class TempoPoint(Base):
    """Time-varying tempo information"""
    __tablename__ = "tempo_points"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    time = Column(Float, nullable=False)  # Time in seconds
    bpm = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="tempo_points")
    
    __table_args__ = (
        Index("idx_tempo_time", "analysis_id", "time"),
    )


class Tag(Base):
    """Tags for categorizing audio files"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    category = Column(String(50))  # e.g., "genre", "mood", "energy"
    created_at = Column(DateTime, default=datetime.utcnow)


class AudioFileTag(Base):
    """Many-to-many relationship between audio files and tags"""
    __tablename__ = "audio_file_tags"
    
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
