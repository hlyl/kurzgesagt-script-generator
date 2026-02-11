"""Tests for audio generation."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.kurzgesagt.core.audio_generator import AudioGenerator, AudioGenerationError


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("src.kurzgesagt.core.audio_generator.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("src.kurzgesagt.core.audio_generator.settings") as mock_settings:
        mock_settings.openai_api_key = "test_api_key"
        yield mock_settings


class TestAudioGeneratorInit:
    """Test AudioGenerator initialization."""

    def test_init_with_api_key(self, mock_openai_client):
        """Test initialization with provided API key."""
        generator = AudioGenerator(api_key="custom_key")

        assert generator.client is not None
        assert generator.model == "tts-1"
        assert generator.voice == "alloy"

    def test_init_with_settings_api_key(self, mock_openai_client, mock_settings):
        """Test initialization uses settings API key when not provided."""
        generator = AudioGenerator()

        assert generator.client is not None

    def test_init_with_custom_model_and_voice(self, mock_openai_client):
        """Test initialization with custom model and voice."""
        generator = AudioGenerator(
            api_key="test_key",
            model="tts-1-hd",
            voice="nova"
        )

        assert generator.model == "tts-1-hd"
        assert generator.voice == "nova"

    def test_init_without_api_key(self, mock_settings):
        """Test initialization fails without API key."""
        mock_settings.openai_api_key = None

        with pytest.raises(ValueError) as exc_info:
            AudioGenerator()

        assert "OPENAI_API_KEY must be set" in str(exc_info.value)

    def test_init_with_placeholder_key(self, mock_settings):
        """Test initialization fails with placeholder API key."""
        mock_settings.openai_api_key = "your_api_key_here"

        with pytest.raises(ValueError) as exc_info:
            AudioGenerator()

        assert "OPENAI_API_KEY must be set" in str(exc_info.value)


class TestGenerateAudioBytes:
    """Test audio bytes generation."""

    def test_generate_audio_bytes_success(self, mock_openai_client):
        """Test successful audio generation."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.read.return_value = b"fake_audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        result = generator.generate_audio_bytes("Hello world")

        assert result == b"fake_audio_data"
        assert mock_openai_client.audio.speech.create.called

    def test_generate_audio_bytes_with_parameters(self, mock_openai_client):
        """Test audio generation with custom parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key", model="tts-1", voice="alloy")

        generator.generate_audio_bytes(
            text="Test text",
            model="tts-1-hd",
            voice="nova",
            speed=1.5
        )

        # Verify the parameters passed to the API
        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args[1]["model"] == "tts-1-hd"
        assert call_args[1]["voice"] == "nova"
        assert call_args[1]["input"] == "Test text"
        assert call_args[1]["speed"] == 1.5

    def test_generate_audio_bytes_with_defaults(self, mock_openai_client):
        """Test audio generation uses default parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key", model="tts-1-hd", voice="echo")

        generator.generate_audio_bytes("Test")

        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args[1]["model"] == "tts-1-hd"
        assert call_args[1]["voice"] == "echo"
        assert call_args[1]["speed"] == 1.0

    def test_generate_audio_bytes_empty_text(self, mock_openai_client):
        """Test error with empty text."""
        generator = AudioGenerator(api_key="test_key")

        with pytest.raises(AudioGenerationError) as exc_info:
            generator.generate_audio_bytes("")

        assert "Text cannot be empty" in str(exc_info.value)

    def test_generate_audio_bytes_whitespace_only(self, mock_openai_client):
        """Test error with whitespace-only text."""
        generator = AudioGenerator(api_key="test_key")

        with pytest.raises(AudioGenerationError) as exc_info:
            generator.generate_audio_bytes("   \n  \t  ")

        assert "Text cannot be empty" in str(exc_info.value)

    def test_generate_audio_bytes_api_error(self, mock_openai_client):
        """Test handling of API errors."""
        mock_openai_client.audio.speech.create.side_effect = Exception("API Error")

        generator = AudioGenerator(api_key="test_key")

        with pytest.raises(AudioGenerationError) as exc_info:
            generator.generate_audio_bytes("Test text")

        assert "Failed to generate audio" in str(exc_info.value)


class TestSaveAudio:
    """Test saving audio to file."""

    def test_save_audio_success(self, mock_openai_client, tmp_path):
        """Test successful audio save."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_content"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        output_path = tmp_path / "output.mp3"
        result_path, duration = generator.save_audio("Test narration", output_path)

        assert result_path == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == b"audio_content"
        assert isinstance(duration, float)
        assert duration > 0

    def test_save_audio_creates_parent_directory(self, mock_openai_client, tmp_path):
        """Test that parent directories are created."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        output_path = tmp_path / "audio" / "scene_01" / "narration.mp3"
        generator.save_audio("Test", output_path)

        assert output_path.parent.exists()
        assert output_path.exists()

    def test_save_audio_with_custom_parameters(self, mock_openai_client, tmp_path):
        """Test save audio with custom parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        output_path = tmp_path / "test.mp3"
        generator.save_audio(
            "Test text",
            output_path,
            model="tts-1-hd",
            voice="shimmer",
            speed=1.25
        )

        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args[1]["model"] == "tts-1-hd"
        assert call_args[1]["voice"] == "shimmer"
        assert call_args[1]["speed"] == 1.25


class TestGenerateSceneAudio:
    """Test scene audio generation."""

    def test_generate_scene_audio_success(self, mock_openai_client, tmp_path):
        """Test successful scene audio generation."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"scene_audio"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        result_path, duration = generator.generate_scene_audio(
            project_dir=tmp_path,
            scene_number=3,
            narration="Scene 3 narration"
        )

        expected_path = tmp_path / "audio" / "scene_03.mp3"
        assert result_path == expected_path
        assert expected_path.exists()
        assert expected_path.read_bytes() == b"scene_audio"
        assert isinstance(duration, float)
        assert duration > 0

    def test_generate_scene_audio_with_parameters(self, mock_openai_client, tmp_path):
        """Test scene audio generation with custom parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        generator.generate_scene_audio(
            project_dir=tmp_path,
            scene_number=1,
            narration="Test",
            model="tts-1-hd",
            voice="onyx",
            speed=0.9
        )

        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args[1]["model"] == "tts-1-hd"
        assert call_args[1]["voice"] == "onyx"
        assert call_args[1]["speed"] == 0.9

    def test_generate_scene_audio_creates_audio_directory(self, mock_openai_client, tmp_path):
        """Test that audio directory is created."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        generator.generate_scene_audio(
            project_dir=tmp_path,
            scene_number=1,
            narration="Test"
        )

        audio_dir = tmp_path / "audio"
        assert audio_dir.exists()
        assert audio_dir.is_dir()


class TestGenerateShotAudio:
    """Test shot audio generation."""

    def test_generate_shot_audio_success(self, mock_openai_client, tmp_path):
        """Test successful shot audio generation."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"shot_audio"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        result_path, duration = generator.generate_shot_audio(
            project_dir=tmp_path,
            scene_number=2,
            shot_number=5,
            narration="Shot narration"
        )

        expected_path = tmp_path / "audio" / "scene_02" / "shot_05.mp3"
        assert result_path == expected_path
        assert expected_path.exists()
        assert expected_path.read_bytes() == b"shot_audio"
        assert isinstance(duration, float)
        assert duration > 0

    def test_generate_shot_audio_creates_directories(self, mock_openai_client, tmp_path):
        """Test that scene subdirectory is created for shots."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        generator.generate_shot_audio(
            project_dir=tmp_path,
            scene_number=4,
            shot_number=2,
            narration="Test"
        )

        scene_dir = tmp_path / "audio" / "scene_04"
        assert scene_dir.exists()
        assert scene_dir.is_dir()

    def test_generate_shot_audio_with_parameters(self, mock_openai_client, tmp_path):
        """Test shot audio generation with custom parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        generator.generate_shot_audio(
            project_dir=tmp_path,
            scene_number=1,
            shot_number=1,
            narration="Test",
            model="tts-1",
            voice="fable",
            speed=1.1
        )

        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args[1]["model"] == "tts-1"
        assert call_args[1]["voice"] == "fable"
        assert call_args[1]["speed"] == 1.1

    def test_generate_shot_audio_numbering(self, mock_openai_client, tmp_path):
        """Test shot audio file naming with zero-padding."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"audio_data"
        mock_openai_client.audio.speech.create.return_value = mock_response

        generator = AudioGenerator(api_key="test_key")

        # Test single digit numbers are zero-padded
        result = generator.generate_shot_audio(
            project_dir=tmp_path,
            scene_number=3,
            shot_number=7,
            narration="Test"
        )

        assert "scene_03" in str(result)
        assert "shot_07" in str(result)
