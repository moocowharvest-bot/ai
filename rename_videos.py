"""
Rename video files starting with P to YYYYMMDD_HHMMSS.mp4
using the video capture date/time from metadata.

Requires ffprobe (part of ffmpeg) to be installed and in PATH.
Download from: https://ffmpeg.org/download.html
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


def get_video_creation_time(video_path: Path) -> datetime | None:
    """Extract creation time from video metadata using ffprobe."""
    try:
        # Use ffprobe to get metadata in JSON format
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_entries', 'format_tags=creation_time',
                str(video_path)
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        
        # Try to get creation_time from format tags
        creation_time_str = data.get('format', {}).get('tags', {}).get('creation_time')
        
        if creation_time_str:
            # Parse ISO format datetime (e.g., "2024-01-15T14:30:45.000000Z")
            # Remove microseconds and Z for easier parsing
            creation_time_str = creation_time_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(creation_time_str)
            return dt
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"  Warning: Could not read metadata from {video_path.name}: {e}")
    
    return None


def get_file_modified_time(video_path: Path) -> datetime:
    """Fallback: use file modification time."""
    timestamp = video_path.stat().st_mtime
    return datetime.fromtimestamp(timestamp)


def rename_video_files(directory: Path = None, dry_run: bool = True):
    """
    Rename video files starting with P to YYYYMMDD_HHMMSS.mp4.
    
    Args:
        directory: Directory to search for videos (default: current directory)
        dry_run: If True, only print what would be renamed without actually renaming
    """
    if directory is None:
        directory = Path.cwd()
    else:
        directory = Path(directory)
    
    # Find all .mp4 files starting with P
    video_files = [f for f in directory.iterdir() if f.is_file() and f.name.startswith('P') and f.suffix.lower() == '.mp4']
    
    if not video_files:
        print(f"No .mp4 files starting with P found in {directory}")
        return
    
    print(f"Found {len(video_files)} video file(s) to process")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (files will be renamed)'}")
    print()
    
    renamed_count = 0
    error_count = 0
    
    for video_file in sorted(video_files):
        try:
            # Try to get creation time from metadata
            creation_time = get_video_creation_time(video_file)
            
            if creation_time is None:
                # Fallback to file modification time
                print(f"  {video_file.name}: Using file modification time as fallback")
                creation_time = get_file_modified_time(video_file)
            
            # Format: YYYYMMDD_HHMMSS.mp4
            new_name = creation_time.strftime("%Y%m%d_%H%M%S.mp4")
            new_path = video_file.parent / new_name
            
            # Check if target file already exists
            if new_path.exists() and new_path != video_file:
                print(f"  {video_file.name} -> {new_name} [SKIPPED: target exists]")
                error_count += 1
                continue
            
            if dry_run:
                print(f"  {video_file.name} -> {new_name} [would rename]")
            else:
                video_file.rename(new_path)
                print(f"  {video_file.name} -> {new_name} [renamed]")
                renamed_count += 1
                
        except Exception as e:
            print(f"  {video_file.name}: ERROR - {e}")
            error_count += 1
    
    print()
    if dry_run:
        print(f"DRY RUN complete. {len(video_files)} file(s) would be processed.")
    else:
        print(f"Renamed {renamed_count} file(s). {error_count} error(s).")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    dry_run = True
    directory = None
    
    if len(sys.argv) > 1:
        if "--execute" in sys.argv or "-x" in sys.argv:
            dry_run = False
            print("WARNING: Files will be actually renamed!")
            response = input("Continue? (yes/no): ")
            if response.lower() not in ('yes', 'y'):
                print("Cancelled.")
                sys.exit(0)
        
        # Get directory from command line if provided
        for arg in sys.argv[1:]:
            if arg not in ("--execute", "-x") and Path(arg).is_dir():
                directory = Path(arg)
                break
    
    if directory is None:
        directory = Path.cwd()
    
    print(f"Processing directory: {directory}")
    print()
    
    rename_video_files(directory, dry_run=dry_run)
    
    if dry_run:
        print()
        print("To actually rename files, run with --execute or -x flag:")
        print(f"  python {Path(__file__).name} --execute")
