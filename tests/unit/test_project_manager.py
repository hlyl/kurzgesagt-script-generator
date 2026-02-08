"""Unit tests for ProjectManager."""

import pytest

from src.kurzgesagt.core import ProjectManager, ProjectNotFoundError
from src.kurzgesagt.utils import ValidationError


def test_create_project(project_manager):
    """Test creating a new project."""
    config = project_manager.create(title="Test Project")
    
    assert config.metadata.title == "Test Project"
    assert project_manager.exists("Test-Project")


def test_create_duplicate_project(project_manager):
    """Test creating duplicate project raises error."""
    project_manager.create(title="Test Project")
    
    with pytest.raises(ValidationError):
        project_manager.create(title="Test Project")


def test_load_project(project_manager, sample_project_config):
    """Test loading existing project."""
    # Save first
    project_manager.save(sample_project_config, "test-project")
    
    # Load
    loaded = project_manager.load("test-project")
    assert loaded.metadata.title == sample_project_config.metadata.title


def test_load_nonexistent_project(project_manager):
    """Test loading non-existent project raises error."""
    with pytest.raises(ProjectNotFoundError):
        project_manager.load("nonexistent")


def test_list_projects(project_manager):
    """Test listing projects."""
    project_manager.create(title="Project 1")
    project_manager.create(title="Project 2")
    
    projects = project_manager.list_projects()
    assert len(projects) == 2


def test_delete_project(project_manager):
    """Test deleting a project."""
    project_manager.create(title="Test Project")
    assert project_manager.exists("Test-Project")
    
    project_manager.delete("Test-Project")
    assert not project_manager.exists("Test-Project")