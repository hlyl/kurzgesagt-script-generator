"""Pytest configuration and fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest

from src.kurzgesagt.core import ProjectManager, ScriptGenerator
from src.kurzgesagt.models import ProjectConfig, ProjectMetadata, Scene, Shot
from tests.mocks.anthropic_mock import MockAnthropicClient


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def sample_project_config():
    """Create sample project configuration."""
    return ProjectConfig(
        metadata=ProjectMetadata(title="Test Project", author="Test Author")
    )


@pytest.fixture
def sample_scene():
    """Create sample scene with shots."""
    return Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=10,
        shots=[
            Shot(
                number=1,
                narration="Test narration",
                duration=5,
                description="Test description",
                image_prompt="Test image prompt",
                video_prompt="Test video prompt",
            )
        ],
    )


@pytest.fixture
def project_manager(temp_dir):
    """Create project manager with temp directory."""
    return ProjectManager(base_path=temp_dir)


@pytest.fixture
def script_generator(temp_dir):
    """Create script generator with temp templates."""
    # Copy templates to temp dir
    templates_src = Path(__file__).parent.parent / "templates"
    templates_dst = temp_dir / "templates"
    shutil.copytree(templates_src, templates_dst)

    return ScriptGenerator(templates_dir=templates_dst)


@pytest.fixture
def templates_dir(temp_dir):
    """Provide templates directory copied into temp dir."""
    templates_src = Path(__file__).parent.parent / "templates"
    templates_dst = temp_dir / "templates"
    shutil.copytree(templates_src, templates_dst)
    return templates_dst


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Fixture to mock Anthropic client."""
    monkeypatch.setattr(
        "src.kurzgesagt.core.providers.anthropic_provider.Anthropic",
        MockAnthropicClient,
    )
