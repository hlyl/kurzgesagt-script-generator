"""Tests for video generation from images."""

from unittest.mock import MagicMock, patch

import pytest

from src.kurzgesagt.core.video_generator import VideoGenerationError, VideoGenerator


@pytest.fixture
def mock_genai_client():
    """Mock Google GenAI client."""
    with patch("src.kurzgesagt.core.video_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        yield mock_client


@pytest.fixture
def temp_image(tmp_path):
    """Create a temporary test image."""
    image_path = tmp_path / "test_image.png"
    image_path.write_bytes(b"fake_png_data")
    return image_path


class TestVideoGeneratorInit:
    """Test VideoGenerator initialization."""

    def test_init_with_api_key(self, mock_genai_client):
        """Test initialization with valid API key."""
        generator = VideoGenerator(api_key="test_key")
        assert generator.client is not None

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(VideoGenerationError) as exc_info:
            VideoGenerator(api_key=None)

        assert "API key is required" in str(exc_info.value)

    def test_init_with_empty_api_key(self):
        """Test initialization fails with empty API key."""
        with pytest.raises(VideoGenerationError) as exc_info:
            VideoGenerator(api_key="")

        assert "API key is required" in str(exc_info.value)


class TestBuildVideoPrompt:
    """Test video prompt building."""

    def test_build_video_prompt_basic(self, mock_genai_client):
        """Test basic prompt building."""
        generator = VideoGenerator(api_key="test_key")

        result = generator._build_video_prompt(
            base_prompt="Show a flowing river",
            key_elements="water, trees, mountains",
            style_context="Vibrant colors with smooth animation",
            duration=8
        )

        assert "Show a flowing river" in result
        assert "water, trees, mountains" in result
        assert "Vibrant colors" in result
        assert "8 seconds" in result
        assert "Camera movement" in result

    def test_build_video_prompt_with_long_style(self, mock_genai_client):
        """Test prompt building limits style context."""
        generator = VideoGenerator(api_key="test_key")

        long_style = "x" * 1000  # Very long style context

        result = generator._build_video_prompt(
            base_prompt="Test prompt",
            key_elements="element1",
            style_context=long_style,
            duration=8
        )

        # Style should be truncated to 500 chars
        style_in_result = [line for line in result.split("\n") if "x" in line][0]
        assert len(style_in_result) <= 500

    def test_build_video_prompt_includes_animation_guidance(self, mock_genai_client):
        """Test prompt includes animation guidance."""
        generator = VideoGenerator(api_key="test_key")

        result = generator._build_video_prompt(
            base_prompt="Test base",
            key_elements="element1",
            style_context="Test style",
            duration=5
        )

        assert "Smooth cinematic motion" in result
        assert "parallax effects" in result
        assert "consistent pacing" in result


class TestGenerateVideoFromImage:
    """Test video generation from image."""

    def test_generate_video_file_not_found(self, mock_genai_client, tmp_path):
        """Test error when image file doesn't exist."""
        generator = VideoGenerator(api_key="test_key")

        nonexistent_path = tmp_path / "nonexistent.png"

        with pytest.raises(VideoGenerationError) as exc_info:
            generator.generate_video_from_image(
                image_path=nonexistent_path,
                video_prompt="Test",
                key_elements=[],
                style_context="Style"
            )

        assert "Failed to read image" in str(exc_info.value)

    def test_generate_video_api_error(self, mock_genai_client, temp_image):
        """Test handling of API errors during generation."""
        mock_genai_client.models.generate_videos.side_effect = Exception("API Error")

        generator = VideoGenerator(api_key="test_key")

        with pytest.raises(VideoGenerationError) as exc_info:
            generator.generate_video_from_image(
                image_path=temp_image,
                video_prompt="Test",
                key_elements=[],
                style_context="Style"
            )

        assert "Failed to start video generation" in str(exc_info.value)

