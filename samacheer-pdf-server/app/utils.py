from pathlib import Path
from datetime import datetime

def get_file_size(file_path: Path) -> dict:
    """Get file size in bytes and MB"""
    size_bytes = file_path.stat().st_size
    size_mb = round(size_bytes / (1024 * 1024), 2)
    
    return {
        "bytes": size_bytes,
        "mb": size_mb
    }

def generate_download_url(filename: str, base_url: str = "http://localhost:8000") -> str:
    """Generate download URL"""
    return f"{base_url}/download/{filename}"

def get_file_creation_time(file_path: Path) -> datetime:
    """Get file creation timestamp"""
    timestamp = file_path.stat().st_ctime
    return datetime.fromtimestamp(timestamp)