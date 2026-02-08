"""Unit tests for data models."""

import pytest
from pydantic import ValidationError

from src.kurzgesagt.models import (
    ProjectConfig,
    ProjectMetadata,
    Scene,
    Shot,
)


def test_shot_creation():
    """Test creating a valid shot."""
    shot = Shot(
        number=1,
        narration="Test narration",
        duration=5,
        description="Test description",
        image_prompt="Test image",
        video_prompt="Test video",
    )

    assert shot.number == 1
    assert shot.duration == 5
    assert not shot.is_nested


def test_shot_validation():
    """Test shot validation rules."""
    with pytest.raises(ValidationError):
        Shot(
            number=0,  # Invalid: must be >= 1
            narration="Test",
            duration=5,
            description="Test",
            image_prompt="Test",
            video_prompt="Test",
        )


def test_scene_title_uppercase():
    """Test scene title is automatically uppercased."""
    scene = Scene(number=1, title="lowercase title", purpose="Test", duration=10)

    assert scene.title == "LOWERCASE TITLE"


def test_project_config_duration_calculation(sample_scene):
    """Test total duration calculation."""
    config = ProjectConfig(
        metadata=ProjectMetadata(title="Test"), scenes=[sample_scene]
    )

    assert config.total_duration == sample_scene.duration


def test_project_yaml_roundtrip(temp_dir, sample_project_config):
    """Test saving and loading from YAML."""
    yaml_path = temp_dir / "test_config.yaml"

    # Save
    sample_project_config.to_yaml(yaml_path)
    assert yaml_path.exists()

    # Load
    loaded = ProjectConfig.from_yaml(yaml_path)
    assert loaded.metadata.title == sample_project_config.metadata.title
