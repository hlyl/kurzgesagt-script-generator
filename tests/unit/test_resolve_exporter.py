"""Tests for DaVinci Resolve export utilities."""

import json
from unittest.mock import patch

import pytest

from src.kurzgesagt.core.resolve_exporter import (
    ResolveExporter,
    ResolveExportError,
)


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create audio directory
    audio_dir = project_dir / "audio"
    audio_dir.mkdir()

    # Create images directory
    images_dir = project_dir / "images"
    images_dir.mkdir()
    scene_dir = images_dir / "scene_01"
    scene_dir.mkdir()
    (scene_dir / "shot_01.png").touch()
    (scene_dir / "shot_02.png").touch()

    # Create videos directory
    videos_dir = project_dir / "videos"
    videos_dir.mkdir()
    scene_video_dir = videos_dir / "scene_01"
    scene_video_dir.mkdir()
    (scene_video_dir / "shot_01.mp4").touch()

    return project_dir


@pytest.fixture
def sample_timeline_data():
    """Sample timeline data for testing."""
    return {
        "project_name": "Test Project",
        "fps": 30,
        "total_duration_ms": 15000,
        "total_duration_timecode": "00:00:15:00",
        "scenes": [
            {
                "scene_number": 1,
                "scene_title": "Introduction",
                "start_ms": 0,
                "start_timecode": "00:00:00:00",
                "shots": [
                    {
                        "shot_number": 1,
                        "start_timecode": "00:00:00:00",
                        "end_timecode": "00:00:05:00",
                        "duration_ms": 5000,
                        "narration_preview": "Welcome to our video"
                    },
                    {
                        "shot_number": 2,
                        "start_timecode": "00:00:05:00",
                        "end_timecode": "00:00:10:00",
                        "duration_ms": 5000,
                        "narration_preview": "This is the second shot"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def exporter_with_data(temp_project_dir, sample_timeline_data):
    """Create exporter with preloaded timeline data."""
    # Write timeline data to file
    timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
    timeline_path.write_text(json.dumps(sample_timeline_data))

    exporter = ResolveExporter(temp_project_dir, fps=30)
    exporter.load_timeline_data()
    return exporter


class TestResolveExporterInit:
    """Test ResolveExporter initialization."""

    def test_init_with_path_object(self, temp_project_dir):
        """Test initialization with Path object."""
        exporter = ResolveExporter(temp_project_dir, fps=30)
        assert exporter.project_dir == temp_project_dir
        assert exporter.fps == 30
        assert exporter.timeline_data is None

    def test_init_with_string_path(self, temp_project_dir):
        """Test initialization with string path."""
        exporter = ResolveExporter(str(temp_project_dir), fps=24)
        assert exporter.project_dir == temp_project_dir
        assert exporter.fps == 24

    def test_init_default_fps(self, temp_project_dir):
        """Test initialization with default FPS."""
        exporter = ResolveExporter(temp_project_dir)
        assert exporter.fps == 30


class TestLoadTimelineData:
    """Test loading timeline data."""

    def test_load_timeline_data_success(self, temp_project_dir, sample_timeline_data):
        """Test successful timeline data loading."""
        # Write timeline data
        timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
        timeline_path.write_text(json.dumps(sample_timeline_data))

        exporter = ResolveExporter(temp_project_dir)
        result = exporter.load_timeline_data()

        assert result == sample_timeline_data
        assert exporter.timeline_data == sample_timeline_data

    def test_load_timeline_data_file_not_found(self, temp_project_dir):
        """Test loading when timeline file doesn't exist."""
        exporter = ResolveExporter(temp_project_dir)

        with pytest.raises(ResolveExportError) as exc_info:
            exporter.load_timeline_data()

        assert "Timeline data not found" in str(exc_info.value)
        assert "Generate full audio first" in str(exc_info.value)

    def test_load_timeline_data_invalid_json(self, temp_project_dir):
        """Test loading invalid JSON data."""
        timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
        timeline_path.write_text("{ invalid json }")

        exporter = ResolveExporter(temp_project_dir)

        with pytest.raises(ResolveExportError) as exc_info:
            exporter.load_timeline_data()

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_timeline_data_read_error(self, temp_project_dir):
        """Test handling of file read errors."""
        timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
        timeline_path.write_text("[]")

        exporter = ResolveExporter(temp_project_dir)

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ResolveExportError) as exc_info:
                exporter.load_timeline_data()

            assert "Failed to load timeline data" in str(exc_info.value)


class TestFormatDurationTimecode:
    """Test timecode formatting."""

    def test_format_duration_simple(self, temp_project_dir):
        """Test formatting simple durations."""
        exporter = ResolveExporter(temp_project_dir, fps=30)

        # Test 5 seconds
        result = exporter._format_duration_timecode(5000, 30)
        assert result == "00:00:05:00"

    def test_format_duration_with_frames(self, temp_project_dir):
        """Test formatting with fractional frames."""
        exporter = ResolveExporter(temp_project_dir, fps=30)

        # Test 5.5 seconds (5s + 15 frames at 30fps)
        result = exporter._format_duration_timecode(5500, 30)
        assert result == "00:00:05:15"

    def test_format_duration_minutes(self, temp_project_dir):
        """Test formatting with minutes."""
        exporter = ResolveExporter(temp_project_dir, fps=30)

        # Test 1 minute 30 seconds
        result = exporter._format_duration_timecode(90000, 30)
        assert result == "00:01:30:00"

    def test_format_duration_hours(self, temp_project_dir):
        """Test formatting with hours."""
        exporter = ResolveExporter(temp_project_dir, fps=30)

        # Test 1 hour 5 minutes 30 seconds
        result = exporter._format_duration_timecode(3930000, 30)
        assert result == "01:05:30:00"


class TestGenerateEDL:
    """Test EDL generation."""

    def test_generate_edl_success(self, exporter_with_data, temp_project_dir):
        """Test successful EDL generation."""
        output_path = temp_project_dir / "exports" / "timeline.edl"

        result = exporter_with_data.generate_edl(output_path)

        assert result == output_path
        assert output_path.exists()

        # Check EDL content
        content = output_path.read_text()
        assert "TITLE: Test Project" in content
        assert "FCM: NON-DROP FRAME" in content
        assert "SCENE 1 - Introduction" in content
        assert "full_narration.mp3" in content

    def test_generate_edl_loads_timeline_data(self, temp_project_dir, sample_timeline_data):
        """Test that generate_edl loads timeline data if not present."""
        timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
        timeline_path.write_text(json.dumps(sample_timeline_data))

        exporter = ResolveExporter(temp_project_dir)
        output_path = temp_project_dir / "exports" / "timeline.edl"

        exporter.generate_edl(output_path)

        assert exporter.timeline_data is not None

    def test_generate_edl_with_video_clips(self, exporter_with_data, temp_project_dir):
        """Test EDL generation with video clips present."""
        output_path = temp_project_dir / "exports" / "timeline.edl"

        exporter_with_data.generate_edl(output_path)
        content = output_path.read_text()

        # Check for video clip references
        assert "scene_01_shot_01.mp4" in content
        assert "stretch to" in content  # Video stretch comment

    def test_generate_edl_with_image_fallback(self, exporter_with_data, temp_project_dir):
        """Test EDL generation falls back to images when video missing."""
        output_path = temp_project_dir / "exports" / "timeline.edl"

        exporter_with_data.generate_edl(output_path)
        content = output_path.read_text()

        # Shot 2 has no video, should reference PNG
        assert "scene_01_shot_02.png" in content

    def test_generate_edl_write_error(self, exporter_with_data, temp_project_dir):
        """Test handling write errors."""
        output_path = temp_project_dir / "exports" / "timeline.edl"

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ResolveExportError) as exc_info:
                exporter_with_data.generate_edl(output_path)

            assert "Failed to generate EDL" in str(exc_info.value)


class TestGenerateFCPXML:
    """Test FCPXML generation."""

    def test_generate_fcpxml_success(self, exporter_with_data, temp_project_dir):
        """Test successful FCPXML generation."""
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        result = exporter_with_data.generate_fcpxml(output_path)

        assert result == output_path
        assert output_path.exists()

        # Check FCPXML content
        content = output_path.read_text()
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert '<fcpxml version="1.9">' in content
        assert '<project name="Test Project_Timeline">' in content
        assert "full_narration.mp3" in content

    def test_generate_fcpxml_loads_timeline_data(self, temp_project_dir, sample_timeline_data):
        """Test that generate_fcpxml loads timeline data if not present."""
        timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
        timeline_path.write_text(json.dumps(sample_timeline_data))

        exporter = ResolveExporter(temp_project_dir)
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        exporter.generate_fcpxml(output_path)

        assert exporter.timeline_data is not None

    def test_generate_fcpxml_with_video_assets(self, exporter_with_data, temp_project_dir):
        """Test FCPXML generation with video assets."""
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        exporter_with_data.generate_fcpxml(output_path)
        content = output_path.read_text()

        # Check for video assets and time-stretch comments
        assert 'asset id="asset1"' in content
        assert "shot_01.mp4" in content
        assert "Time-stretch" in content

    def test_generate_fcpxml_with_image_fallback(self, exporter_with_data, temp_project_dir):
        """Test FCPXML generation falls back to images."""
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        exporter_with_data.generate_fcpxml(output_path)
        content = output_path.read_text()

        # Shot 2 should reference image
        assert "shot_02.png" in content

    def test_generate_fcpxml_format_settings(self, exporter_with_data, temp_project_dir):
        """Test FCPXML format settings."""
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        exporter_with_data.generate_fcpxml(output_path)
        content = output_path.read_text()

        # Check format settings
        assert 'frameDuration="1/30s"' in content
        assert 'width="1920"' in content
        assert 'height="1080"' in content

    def test_generate_fcpxml_markers(self, exporter_with_data, temp_project_dir):
        """Test FCPXML scene markers."""
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        exporter_with_data.generate_fcpxml(output_path)
        content = output_path.read_text()

        # Check for scene markers
        assert '<marker start="00:00:00:00"' in content
        assert 'value="Scene 1: Introduction"' in content

    def test_generate_fcpxml_write_error(self, exporter_with_data, temp_project_dir):
        """Test handling write errors."""
        output_path = temp_project_dir / "exports" / "timeline.fcpxml"

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ResolveExportError) as exc_info:
                exporter_with_data.generate_fcpxml(output_path)

            assert "Failed to generate FCPXML" in str(exc_info.value)


class TestGenerateResolveScript:
    """Test Resolve Python script generation."""

    def test_generate_resolve_script_success(self, exporter_with_data, temp_project_dir):
        """Test successful Resolve script generation."""
        output_path = temp_project_dir / "exports" / "import_to_resolve.py"

        result = exporter_with_data.generate_resolve_script(output_path)

        assert result == output_path
        assert output_path.exists()

        # Check file is executable
        assert output_path.stat().st_mode & 0o111  # Check execute bits

        # Check script content
        content = output_path.read_text()
        assert "#!/usr/bin/env python3" in content
        assert "DaVinciResolveScript" in content
        assert "Test Project" in content
        assert "full_narration.mp3" in content

    def test_generate_resolve_script_loads_timeline_data(self, temp_project_dir, sample_timeline_data):
        """Test that generate_resolve_script loads timeline data if not present."""
        timeline_path = temp_project_dir / "audio" / "timeline_timestamps.json"
        timeline_path.write_text(json.dumps(sample_timeline_data))

        exporter = ResolveExporter(temp_project_dir)
        output_path = temp_project_dir / "exports" / "import_to_resolve.py"

        exporter.generate_resolve_script(output_path)

        assert exporter.timeline_data is not None

    def test_generate_resolve_script_content_structure(self, exporter_with_data, temp_project_dir):
        """Test Resolve script structure and content."""
        output_path = temp_project_dir / "exports" / "import_to_resolve.py"

        exporter_with_data.generate_resolve_script(output_path)
        content = output_path.read_text()

        # Check for required script sections
        assert "import sys" in content
        assert "import json" in content
        assert "import DaVinciResolveScript" in content
        assert "timeline_timestamps.json" in content
        assert "CreateProject" in content
        assert "GetMediaPool" in content
        assert "AddSubFolder" in content
        assert "CreateEmptyTimeline" in content
        assert "AddMarker" in content

    def test_generate_resolve_script_scene_bins(self, exporter_with_data, temp_project_dir):
        """Test Resolve script creates scene bins."""
        output_path = temp_project_dir / "exports" / "import_to_resolve.py"

        exporter_with_data.generate_resolve_script(output_path)
        content = output_path.read_text()

        # Check for scene bin creation logic (dynamic, not hardcoded)
        assert 'bin_name = f"Scene {scene_num}: {scene_title}"' in content
        assert "AddSubFolder" in content

    def test_generate_resolve_script_video_and_image_handling(self, exporter_with_data, temp_project_dir):
        """Test script handles both videos and images."""
        output_path = temp_project_dir / "exports" / "import_to_resolve.py"

        exporter_with_data.generate_resolve_script(output_path)
        content = output_path.read_text()

        # Check for video/image handling
        assert "shot_01.mp4" in content or "video_path" in content
        assert "shot_02.png" in content or "image_path" in content
        assert "Adjust speed to" in content  # Speed adjustment note

    def test_generate_resolve_script_write_error(self, exporter_with_data, temp_project_dir):
        """Test handling write errors."""
        output_path = temp_project_dir / "exports" / "import_to_resolve.py"

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ResolveExportError) as exc_info:
                exporter_with_data.generate_resolve_script(output_path)

            assert "Failed to generate Resolve script" in str(exc_info.value)
