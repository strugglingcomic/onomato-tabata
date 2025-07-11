#!/usr/bin/env python3
"""
BPM Analyzer CLI interface
"""
from pathlib import Path
from typing import Optional, List
from enum import Enum

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from bpm_analyzer.core.analyzer import analyze_file
from bpm_analyzer.processors.batch import BatchProcessor
from bpm_analyzer.config import AnalysisConfig
from bpm_analyzer.db.database import AnalysisDB

# Initialize Typer app and Rich console
app = typer.Typer(
    name="bpm-analyzer",
    help="High-precision audio tempo analysis for workout synchronization",
    add_completion=False,
)
console = Console()


class Algorithm(str, Enum):
    """Supported BPM detection algorithms"""
    madmom = "madmom"
    essentia = "essentia"
    librosa = "librosa"
    aubio = "aubio"
    ensemble = "ensemble"


class OutputFormat(str, Enum):
    """Supported output formats"""
    jams = "jams"
    csv = "csv"
    json = "json"


@app.command()
def analyze(
    audio_file: Path = typer.Argument(
        ..., 
        help="Path to audio file to analyze",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file path (default: input_file.jams)",
    ),
    algorithm: Algorithm = typer.Option(
        Algorithm.madmom,
        "--algorithm", "-a",
        help="BPM detection algorithm to use",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.jams,
        "--format", "-f",
        help="Output format",
    ),
    confidence_threshold: float = typer.Option(
        0.0,
        "--confidence", "-c",
        min=0.0,
        max=1.0,
        help="Minimum confidence threshold for beats",
    ),
    tempo_min: int = typer.Option(
        30,
        "--tempo-min",
        help="Minimum tempo to consider (BPM)",
    ),
    tempo_max: int = typer.Option(
        300,
        "--tempo-max",
        help="Maximum tempo to consider (BPM)",
    ),
    db: Optional[str] = typer.Option(
        None,
        "--db",
        help="Database connection string for storing results",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output",
    ),
):
    """Analyze a single audio file for BPM and beat information."""
    
    # Configure analysis
    config = AnalysisConfig(
        algorithm=algorithm.value,
        confidence_threshold=confidence_threshold,
        tempo_range=(tempo_min, tempo_max),
        verbose=verbose,
    )
    
    # Set default output path if not specified
    if output is None:
        output = audio_file.with_suffix(f".{format.value}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Analyzing {audio_file.name}...", total=None)
            
            # Perform analysis
            result = analyze_file(audio_file, config)
            
            progress.update(task, description=f"Writing results to {output}...")
            
            # Save results
            result.save(output, format=format.value)
            
            # Store in database if requested
            if db:
                progress.update(task, description="Storing in database...")
                database = AnalysisDB(db)
                database.store_analysis(result)
            
        # Display summary
        console.print(f"[green]✓[/green] Analysis complete!")
        console.print(f"  Average BPM: [bold]{result.average_bpm:.1f}[/bold]")
        console.print(f"  Total beats: [bold]{len(result.beats)}[/bold]")
        console.print(f"  Duration: [bold]{result.duration:.1f}s[/bold]")
        console.print(f"  Output: {output}")
        if db:
            console.print(f"  Stored in database: {db}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ...,
        help="Directory containing audio files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output_dir: Path = typer.Option(
        Path("./tempo_maps"),
        "--output-dir", "-o",
        help="Directory for output files",
    ),
    pattern: str = typer.Option(
        "*",
        "--pattern", "-p",
        help="File pattern to match (e.g., '*.mp3')",
    ),
    algorithm: Algorithm = typer.Option(
        Algorithm.madmom,
        "--algorithm", "-a",
        help="BPM detection algorithm to use",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.jams,
        "--format", "-f",
        help="Output format",
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        help="Enable parallel processing",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers", "-w",
        help="Number of parallel workers (default: CPU count)",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Process subdirectories recursively",
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--overwrite",
        help="Skip files that already have output",
    ),
    db: Optional[str] = typer.Option(
        None,
        "--db",
        help="Database connection string for storing results",
    ),
):
    """Batch process multiple audio files."""
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure batch processor
    processor = BatchProcessor(
        algorithm=algorithm.value,
        output_format=format.value,
        parallel=parallel,
        num_workers=workers,
        skip_existing=skip_existing,
        database_url=db,
    )
    
    try:
        # Find audio files
        files = list(processor.find_audio_files(
            input_dir, 
            pattern=pattern,
            recursive=recursive
        ))
        
        if not files:
            console.print(f"[yellow]No audio files found matching '{pattern}'[/yellow]")
            return
        
        console.print(f"Found [bold]{len(files)}[/bold] audio files to process")
        
        # Process files
        results = processor.process_files(files, output_dir)
        
        # Display summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        # Create summary table
        table = Table(title="Batch Processing Summary")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        
        table.add_row("[green]Successful[/green]", str(successful))
        if failed > 0:
            table.add_row("[red]Failed[/red]", str(failed))
        if skip_existing and processor.skipped_count > 0:
            table.add_row("[yellow]Skipped[/yellow]", str(processor.skipped_count))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Batch processing error: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def db(
    action: str = typer.Argument(
        ...,
        help="Database action: init, query, stats, export"
    ),
    database: str = typer.Option(
        "sqlite:///music_tempo.db",
        "--database", "-d",
        help="Database connection string",
    ),
    min_bpm: Optional[float] = typer.Option(
        None,
        "--min-bpm",
        help="Minimum BPM for queries",
    ),
    max_bpm: Optional[float] = typer.Option(
        None,
        "--max-bpm",
        help="Maximum BPM for queries",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file for export",
    ),
):
    """Database operations for tempo analysis results."""
    
    db_instance = AnalysisDB(database)
    
    if action == "init":
        db_instance.init_db()
        console.print(f"[green]✓[/green] Database initialized at {database}")
        
    elif action == "query":
        results = db_instance.query_tempo_range(min_bpm=min_bpm, max_bpm=max_bpm)
        
        table = Table(title=f"Songs with BPM {min_bpm or 0} - {max_bpm or 300}")
        table.add_column("File", style="bold")
        table.add_column("BPM", justify="right")
        table.add_column("Beats", justify="right")
        table.add_column("Duration", justify="right")
        
        for r in results[:20]:  # Show first 20
            table.add_row(
                Path(r.audio_file.file_path).name,
                f"{r.average_bpm:.1f}",
                str(r.beat_count),
                f"{r.audio_file.duration:.1f}s"
            )
        
        console.print(table)
        if len(results) > 20:
            console.print(f"... and {len(results) - 20} more")
            
    elif action == "stats":
        stats = db_instance.get_statistics()
        
        table = Table(title="Database Statistics")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        
        for key, value in stats.items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)
        
    elif action == "export":
        if not output:
            output = Path("tempo_export.csv")
        
        count = db_instance.export_to_csv(output)
        console.print(f"[green]✓[/green] Exported {count} entries to {output}")
        
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: init, query, stats, export")
        raise typer.Exit(code=1)


@app.command()
def info():
    """Display information about available algorithms and formats."""
    
    # Algorithms table
    algo_table = Table(title="Available Algorithms")
    algo_table.add_column("Algorithm", style="bold")
    algo_table.add_column("Description")
    algo_table.add_column("Accuracy", justify="center")
    algo_table.add_column("Speed", justify="center")
    
    algo_table.add_row(
        "madmom",
        "Machine learning-based (DBN)",
        "[green]★★★★★[/green]",
        "[yellow]★★★[/yellow]"
    )
    algo_table.add_row(
        "essentia",
        "Multi-feature extraction",
        "[green]★★★★[/green]",
        "[green]★★★★[/green]"
    )
    algo_table.add_row(
        "librosa",
        "Onset-based detection",
        "[yellow]★★★[/yellow]",
        "[green]★★★★★[/green]"
    )
    algo_table.add_row(
        "aubio",
        "Real-time optimized",
        "[yellow]★★★[/yellow]",
        "[green]★★★★★[/green]"
    )
    algo_table.add_row(
        "ensemble",
        "Combined approach",
        "[green]★★★★★[/green]",
        "[yellow]★★[/yellow]"
    )
    
    console.print(algo_table)
    console.print()
    
    # Formats table
    format_table = Table(title="Output Formats")
    format_table.add_column("Format", style="bold")
    format_table.add_column("Description")
    format_table.add_column("Use Case")
    
    format_table.add_row(
        "jams",
        "JSON Annotated Music Specification",
        "Full annotations with confidence"
    )
    format_table.add_row(
        "csv",
        "Comma-separated values",
        "Spreadsheet analysis"
    )
    format_table.add_row(
        "json",
        "JavaScript Object Notation",
        "Web applications"
    )
    
    console.print(format_table)


@app.command()
def validate(
    audio_file: Path = typer.Argument(
        ...,
        help="Audio file to validate",
        exists=True,
    ),
    reference: Optional[Path] = typer.Option(
        None,
        "--reference", "-r",
        help="Reference annotation file for comparison",
    ),
):
    """Validate audio file and optionally compare with reference."""
    
    try:
        from bpm_analyzer.utils.validation import validate_audio_file
        
        with console.status("Validating audio file..."):
            validation_result = validate_audio_file(audio_file)
        
        if validation_result.is_valid:
            console.print(f"[green]✓[/green] Audio file is valid")
            console.print(f"  Format: [bold]{validation_result.format}[/bold]")
            console.print(f"  Duration: [bold]{validation_result.duration:.1f}s[/bold]")
            console.print(f"  Sample rate: [bold]{validation_result.sample_rate}Hz[/bold]")
            console.print(f"  Channels: [bold]{validation_result.channels}[/bold]")
        else:
            console.print(f"[red]✗[/red] Audio file validation failed")
            console.print(f"  Error: {validation_result.error}")
            
        if reference:
            # TODO: Implement reference comparison
            console.print("[yellow]Reference comparison not yet implemented[/yellow]")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Validation error: {str(e)}")
        raise typer.Exit(code=1)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version", "-V",
        help="Show version and exit",
    ),
):
    """
    BPM Analyzer - High-precision audio tempo analysis
    
    Extract beat-by-beat tempo information from audio files with
    multiple algorithm options and output formats.
    """
    if version:
        from bpm_analyzer.version import __version__
        console.print(f"BPM Analyzer version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
