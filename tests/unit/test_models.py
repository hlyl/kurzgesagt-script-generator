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


def test_scene_shot_count():
    """Test scene shot_count property."""
    shot1 = Shot(
        number=1,
        narration="Shot 1",
        duration=5.0,
        description="Test shot 1",
        image_prompt="Image 1",
        video_prompt="Video 1",
        key_elements=[],
    )
    shot2 = Shot(
        number=2,
        narration="Shot 2",
        duration=6.0,
        description="Test shot 2",
        image_prompt="Image 2",
        video_prompt="Video 2",
        key_elements=[],
    )
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=11.5,
        shots=[shot1, shot2],
    )

    assert scene.shot_count == 2


def test_scene_add_shot():
    """Test scene add_shot method."""
    shot = Shot(
        number=1,
        narration="Test shot",
        duration=5.0,
        description="Test shot",
        image_prompt="Image",
        video_prompt="Video",
        key_elements=[],
    )
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=5.0,
        shots=[],
    )

    scene.add_shot(shot)
    assert scene.shot_count == 1
    assert scene.shots[0] == shot


def test_scene_calculate_duration():
    """Test scene calculate_duration method."""
    shot1 = Shot(
        number=1,
        narration="Shot 1",
        duration=5.0,
        description="Test shot 1",
        image_prompt="Image 1",
        video_prompt="Video 1",
        key_elements=[],
        transition_duration=0.5,
    )
    shot2 = Shot(
        number=2,
        narration="Shot 2",
        duration=6.0,
        description="Test shot 2",
        image_prompt="Image 2",
        video_prompt="Video 2",
        key_elements=[],
        transition_duration=0.5,
    )
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=5.0,  # Will be recalculated
        shots=[shot1, shot2],
    )

    # Calculate: 5.0 + 0.5 (transition) + 6.0 = 11.5
    calculated = scene.calculate_duration()
    assert calculated == 11.5


def test_scene_calculate_duration_empty_shots():
    """Test scene calculate_duration with no shots."""
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=0.1,  # Minimum valid duration
        shots=[],
    )

    calculated = scene.calculate_duration()
    assert calculated == 0.0


def test_project_config_scene_count():
    """Test project scene_count property."""
    scene1 = Scene(
        number=1,
        title="SCENE 1",
        purpose="Test purpose 1",
        duration=5.0,
        shots=[],
    )
    scene2 = Scene(
        number=2,
        title="SCENE 2",
        purpose="Test purpose 2",
        duration=6.0,
        shots=[],
    )
    config = ProjectConfig(
        metadata=ProjectMetadata(title="Test"),
        scenes=[scene1, scene2]
    )

    assert config.scene_count == 2


def test_project_config_shot_count():
    """Test project shot_count property."""
    shot1 = Shot(
        number=1,
        narration="Shot 1",
        duration=5.0,
        description="Test shot 1",
        image_prompt="Image 1",
        video_prompt="Video 1",
        key_elements=[],
    )
    shot2 = Shot(
        number=2,
        narration="Shot 2",
        duration=6.0,
        description="Test shot 2",
        image_prompt="Image 2",
        video_prompt="Video 2",
        key_elements=[],
    )
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=11.5,
        shots=[shot1, shot2],
    )
    config = ProjectConfig(
        metadata=ProjectMetadata(title="Test"),
        scenes=[scene]
    )

    assert config.shot_count == 2

