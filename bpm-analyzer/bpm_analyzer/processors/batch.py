"""
Batch processing for multiple audio files
"""
from pathlib import Path
from typing import List, Optional, Generator, Union
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

from rich.progress import Progress, TaskID
from rich.console import Console

from bpm_analyzer.core.analyzer import analyze_file, AnalysisResult
from bpm_analyzer.config import AnalysisConfig
from bpm_analyzer.db.database import AnalysisDB
from bpm_analyzer.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class BatchResult:
    """Result from batch processing"""
    file_path: Path
    success: bool
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class BatchProcessor:
    """Process multiple audio files in batch"""
    
    def __init__(
        self,
        algorithm: str = "madmom",
        output_format: str = "jams",
        parallel: bool = True,
        num_workers: Optional[int] = None,
        skip_existing: bool = True,
        database_url: Optional[str] = None,
    ):
        """
        Initialize batch processor.
        
        Args:
            algorithm: BPM detection algorithm to use
            output_format: Output format for results
            parallel: Use parallel processing
            num_workers: Number of parallel workers (None = CPU count)
            skip_existing: Skip files that already have output
            database_url: Optional database for storing results
        """
        self.algorithm = algorithm
        self.output_format = output_format
        self.parallel = parallel
        self.num_workers = num_workers or mp.cpu_count()
        self.skip_existing = skip_existing
        self.database_url = database_url
        self.skipped_count = 0
        
        # Initialize database if URL provided
        self.db = AnalysisDB(database_url) if database_url else None
        
    def find_audio_files(
        self,
        input_dir: Path,
        pattern: str = "*",
        recursive: bool = True,
    ) -> Generator[Path, None, None]:
        """
        Find audio files in directory.
        
        Args:
            input_dir: Directory to search
            pattern: File pattern to match
            recursive: Search subdirectories
            
        Yields:
            Audio file paths
        """
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg'}
        
        if recursive:
            files = input_dir.rglob(pattern)
        else:
            files = input_dir.glob(pattern)
        
        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                yield file_path
    
    def process_files(
        self,
        files: List[Path],
        output_dir: Path,
    ) -> List[BatchResult]:
        """
        Process multiple audio files.
        
        Args:
            files: List of audio files to process
            output_dir: Directory for output files
            
        Returns:
            List of batch results
        """
        if self.parallel and len(files) > 1:
            return self._process_parallel(files, output_dir)
        else:
            return self._process_sequential(files, output_dir)
    
    def _process_sequential(
        self,
        files: List[Path],
        output_dir: Path,
    ) -> List[BatchResult]:
        """Process files sequentially"""
        results = []
        
        with Progress() as progress:
            task = progress.add_task(
                f"Processing {len(files)} files...",
                total=len(files)
            )
            
            for file_path in files:
                result = self._process_single_file(file_path, output_dir)
                results.append(result)
                progress.update(task, advance=1)
        
        return results
    
    def _process_parallel(
        self,
        files: List[Path],
        output_dir: Path,
    ) -> List[BatchResult]:
        """Process files in parallel"""
        results = []
        
        with Progress() as progress:
            task = progress.add_task(
                f"Processing {len(files)} files...",
                total=len(files)
            )
            
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(
                        self._process_single_file, file_path, output_dir
                    ): file_path
                    for file_path in files
                }
                
                # Process completed tasks
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to process {file_path}: {e}")
                        results.append(
                            BatchResult(
                                file_path=file_path,
                                success=False,
                                error=str(e)
                            )
                        )
                    progress.update(task, advance=1)
        
        return results
    
    def _process_single_file(
        self,
        file_path: Path,
        output_dir: Path,
    ) -> BatchResult:
        """Process a single audio file"""
        try:
            # Check if output already exists
            output_path = self._get_output_path(file_path, output_dir)
            if self.skip_existing and output_path.exists():
                self.skipped_count += 1
                logger.info(f"Skipping {file_path.name} (output exists)")
                return BatchResult(
                    file_path=file_path,
                    success=True,
                    error="Skipped (output exists)"
                )
            
            # Analyze file
            config = AnalysisConfig(algorithm=self.algorithm)
            result = analyze_file(file_path, config)
            
            # Save results
            result.save(output_path, format=self.output_format)
            
            # Store in database if configured
            if self.db:
                self.db.store_analysis(result)
            
            return BatchResult(
                file_path=file_path,
                success=True,
                result=result
            )
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return BatchResult(
                file_path=file_path,
                success=False,
                error=str(e)
            )
    
    def _get_output_path(self, input_path: Path, output_dir: Path) -> Path:
        """Get output path for input file"""
        # Preserve directory structure if configured
        relative_path = input_path.name
        output_path = output_dir / relative_path
        return output_path.with_suffix(f".{self.output_format}")
