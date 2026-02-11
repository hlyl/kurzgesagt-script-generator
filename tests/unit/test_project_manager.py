"""Unit tests for ProjectManager."""

import pytest

from src.kurzgesagt.core import ProjectNotFoundError
from src.kurzgesagt.models import Scene, Shot
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


def test_update_shot_duration(project_manager, sample_project_config):
    """Test updating shot duration updates shot and recalculates scene."""
    # Create a project with scenes and shots
    shot1 = Shot(
        number=1,
        narration="First shot narration",
        duration=5.0,
        description="First shot",
        image_prompt="Image 1",
        video_prompt="Video 1",
        key_elements=[],
    )
    shot2 = Shot(
        number=2,
        narration="Second shot narration",
        duration=6.0,
        description="Second shot",
        image_prompt="Image 2",
        video_prompt="Video 2",
        key_elements=[],
    )
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=11.5,  # 5.0 + 0.5 (transition) + 6.0
        shots=[shot1, shot2],
    )
    sample_project_config.scenes = [scene]

    project_manager.save(sample_project_config, "test-project")

    # Update shot duration
    project_manager.update_shot_duration(
        project_name="test-project",
        scene_number=1,
        shot_number=1,
        actual_duration=7.5,
    )

    # Load and verify
    loaded = project_manager.load("test-project")
    assert loaded.scenes[0].shots[0].duration == 7.5
    # Scene duration should be recalculated: 7.5 + 0.5 (transition) + 6.0 = 14.0
    assert loaded.scenes[0].duration == 14.0


def test_update_shot_duration_nonexistent_project(project_manager):
    """Test updating shot duration for non-existent project raises error."""
    with pytest.raises(ProjectNotFoundError):
        project_manager.update_shot_duration(
            project_name="nonexistent",
            scene_number=1,
            shot_number=1,
            actual_duration=5.0,
        )


def test_update_shot_duration_nonexistent_scene(project_manager, sample_project_config):
    """Test updating shot duration for non-existent scene raises error."""
    project_manager.save(sample_project_config, "test-project")

    with pytest.raises(ValueError, match="Scene 999 not found"):
        project_manager.update_shot_duration(
            project_name="test-project",
            scene_number=999,
            shot_number=1,
            actual_duration=5.0,
        )


def test_update_shot_duration_nonexistent_shot(project_manager, sample_project_config):
    """Test updating shot duration for non-existent shot raises error."""
    shot = Shot(
        number=1,
        narration="Test narration",
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
        shots=[shot],
    )
    sample_project_config.scenes = [scene]
    project_manager.save(sample_project_config, "test-project")

    with pytest.raises(ValueError, match="Shot 999 not found"):
        project_manager.update_shot_duration(
            project_name="test-project",
            scene_number=1,
            shot_number=999,
            actual_duration=5.0,
        )


def test_update_scene_duration(project_manager, sample_project_config):
    """Test updating scene duration."""
    shot = Shot(
        number=1,
        narration="Test narration",
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
        shots=[shot],
    )
    sample_project_config.scenes = [scene]

    project_manager.save(sample_project_config, "test-project")

    # Update scene duration
    project_manager.update_scene_duration(
        project_name="test-project",
        scene_number=1,
        actual_duration=10.5,
    )

    # Load and verify
    loaded = project_manager.load("test-project")
    assert loaded.scenes[0].duration == 10.5


def test_update_scene_duration_nonexistent_scene(project_manager, sample_project_config):
    """Test updating scene duration for non-existent scene raises error."""
    project_manager.save(sample_project_config, "test-project")

    with pytest.raises(ValueError, match="Scene 999 not found"):
        project_manager.update_scene_duration(
            project_name="test-project",
            scene_number=999,
            actual_duration=10.0,
        )


def test_update_transition_durations(project_manager, sample_project_config):
    """Test updating all transition durations in project."""
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
    scene1 = Scene(
        number=1,
        title="SCENE 1",
        purpose="Test purpose 1",
        duration=11.5,
        shots=[shot1, shot2],
        transition_duration=1.0,
    )
    scene2 = Scene(
        number=2,
        title="SCENE 2",
        purpose="Test purpose 2",
        duration=5.0,
        shots=[shot1],
        transition_duration=1.0,
    )
    sample_project_config.scenes = [scene1, scene2]

    project_manager.save(sample_project_config, "test-project")

    # Update transition durations
    project_manager.update_transition_durations(
        project_name="test-project",
        shot_transition=0.75,
        scene_transition=1.5,
    )

    # Load and verify
    loaded = project_manager.load("test-project")

    # Check scene transitions
    assert loaded.scenes[0].transition_duration == 1.5
    assert loaded.scenes[1].transition_duration == 1.5

    # Check shot transitions
    assert loaded.scenes[0].shots[0].transition_duration == 0.75
    assert loaded.scenes[0].shots[1].transition_duration == 0.75
    assert loaded.scenes[1].shots[0].transition_duration == 0.75


def test_update_transition_durations_nonexistent_project(project_manager):
    """Test updating transition durations for non-existent project raises error."""
    with pytest.raises(ProjectNotFoundError):
        project_manager.update_transition_durations(
            project_name="nonexistent",
            shot_transition=0.5,
            scene_transition=1.0,
        )

