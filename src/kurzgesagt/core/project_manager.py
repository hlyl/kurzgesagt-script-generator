"""Project management functionality."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..config import settings
from ..models import ProjectConfig
from ..utils import (
    ValidationError,
    delete_project,
    ensure_directory,
    get_project_path,
    list_project_directories,
    validate_project_identifier,
    validate_project_name,
)


class ProjectNotFoundError(Exception):
    """Raised when project is not found."""

    pass


class ProjectManager:
    """Manages project CRUD operations."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize project manager.

        Args:
            base_path: Base directory for projects (defaults to settings)
        """
        self.base_path = base_path or settings.projects_dir
        ensure_directory(self.base_path)

    def create(self, title: str, author: Optional[str] = None) -> ProjectConfig:
        """
        Create a new project.

        Args:
            title: Project title
            author: Project author

        Returns:
            New ProjectConfig instance

        Raises:
            ValidationError: If project name is invalid or already exists
        """
        # Validate and sanitize name
        project_name = validate_project_name(title)
        project_path = get_project_path(self.base_path, project_name)

        # Check if already exists
        if project_path.exists():
            raise ValidationError(f"Project '{project_name}' already exists")

        # Create project
        config = ProjectConfig.create_new(title=title, author=author)

        # Save to disk
        self.save(config, project_name)

        return config

    def load(self, project_name: str) -> ProjectConfig:
        """
        Load an existing project.

        Args:
            project_name: Name of project to load

        Returns:
            Loaded ProjectConfig

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        validate_project_identifier(project_name)
        project_path = get_project_path(self.base_path, project_name)
        config_file = project_path / "project_config.yaml"

        if not config_file.exists():
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        return ProjectConfig.from_yaml(config_file)

    def save(self, config: ProjectConfig, project_name: Optional[str] = None) -> Path:
        """
        Save project configuration.

        Args:
            config: ProjectConfig to save
            project_name: Optional project name (derived from title if not provided)

        Returns:
            Path to saved project directory
        """
        # Determine project name
        if project_name is None:
            project_name = validate_project_name(config.metadata.title)

        # Create project directory
        project_path = get_project_path(self.base_path, project_name)
        ensure_directory(project_path)

        # Update timestamp
        config.metadata.updated_at = datetime.now()

        # Save configuration
        config_file = project_path / "project_config.yaml"
        config.to_yaml(config_file)

        # Save voice-over script separately if present
        if config.voice_over_script:
            script_file = project_path / "voice_over.txt"
            script_file.write_text(config.voice_over_script, encoding="utf-8")

        return project_path

    def delete(self, project_name: str) -> None:
        """
        Delete a project.

        Args:
            project_name: Name of project to delete

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        validate_project_identifier(project_name)
        project_path = get_project_path(self.base_path, project_name)

        if not project_path.exists():
            raise ProjectNotFoundError(f"Project '{project_name}' not found")

        delete_project(self.base_path, project_name)

    def list_projects(self) -> List[str]:
        """
        List all available projects.

        Returns:
            List of project names
        """
        return list_project_directories(self.base_path)

    def exists(self, project_name: str) -> bool:
        """
        Check if project exists.

        Args:
            project_name: Project name to check

        Returns:
            True if project exists
        """
        project_path = get_project_path(self.base_path, project_name)
        config_file = project_path / "project_config.yaml"
        return config_file.exists()

    def export_metadata(self, project_name: str) -> dict:
        """
        Export project metadata without loading full config.

        Args:
            project_name: Project name

        Returns:
            Dictionary with metadata
        """
        try:
            config = self.load(project_name)
            return {
                "name": project_name,
                "title": config.metadata.title,
                "description": config.metadata.description,
                "created_at": config.metadata.created_at.isoformat(),
                "updated_at": config.metadata.updated_at.isoformat(),
                "scene_count": config.scene_count,
                "shot_count": config.shot_count,
                "duration": config.total_duration,
            }
        except Exception:
            return {"name": project_name, "error": "Failed to load metadata"}
