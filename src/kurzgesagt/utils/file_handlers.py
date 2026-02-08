"""File handling utilities."""

from pathlib import Path
from typing import Optional, List
import shutil
import json


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The created/existing path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write_text(path: Path, content: str, backup: bool = True) -> None:
    """
    Safely write text to file with optional backup.
    
    Args:
        path: File path
        content: Content to write
        backup: Whether to create backup of existing file
    """
    # Create backup if file exists
    if backup and path.exists():
        backup_path = path.with_suffix(path.suffix + '.backup')
        shutil.copy2(path, backup_path)
    
    # Ensure parent directory exists
    ensure_directory(path.parent)
    
    # Write content
    path.write_text(content, encoding='utf-8')


def list_project_directories(base_path: Path) -> List[str]:
    """
    List all project directories.
    
    Args:
        base_path: Base projects directory
        
    Returns:
        List of project directory names
    """
    if not base_path.exists():
        return []
    
    return [
        d.name for d in base_path.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ]


def get_project_path(base_path: Path, project_name: str) -> Path:
    """
    Get full path to project directory.
    
    Args:
        base_path: Base projects directory
        project_name: Project name
        
    Returns:
        Full project path
    """
    return base_path / project_name


def delete_project(base_path: Path, project_name: str) -> None:
    """
    Delete a project directory.
    
    Args:
        base_path: Base projects directory
        project_name: Project name to delete
    """
    project_path = get_project_path(base_path, project_name)
    if project_path.exists():
        shutil.rmtree(project_path)