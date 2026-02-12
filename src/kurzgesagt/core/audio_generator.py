"""Audio generation utilities for text-to-speech."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    PYDUB_AVAILABLE = False

from ..config import settings
from ..utils import ensure_directory, get_logger

logger = get_logger("audio_generator")


class AudioGenerationError(RuntimeError):
    """Raised when audio generation fails."""


class AudioGenerator:
    """Generate audio from text using OpenAI TTS and save to disk."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",
        voice: str = "alloy",
    ) -> None:
        """Initialize audio generator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: TTS model to use ("tts-1" or "tts-1-hd")
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        """
        resolved_key = api_key or settings.openai_api_key
        if not resolved_key or resolved_key == "your_api_key_here":
            raise ValueError("OPENAI_API_KEY must be set for audio generation.")
        self.client = OpenAI(api_key=resolved_key)
        self.model = model
        self.voice = voice

    def generate_audio_bytes(
        self,
        text: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> bytes:
        """Generate audio from text and return bytes.

        Args:
            text: Text to convert to speech
            model: TTS model override
            voice: Voice override
            speed: Speech speed (0.25 to 4.0)

        Returns:
            Audio bytes in MP3 format
        """
        if not text or not text.strip():
            raise AudioGenerationError("Text cannot be empty")

        model_name = model or self.model
        voice_name = voice or self.voice

        logger.info(
            "Generating audio: model=%s voice=%s speed=%s text_length=%d",
            model_name,
            voice_name,
            speed,
            len(text),
        )

        try:
            response = self.client.audio.speech.create(
                model=model_name,
                voice=voice_name,
                input=text,
                speed=speed,
            )

            # Read the audio bytes from the streaming response
            audio_bytes = response.read()
            logger.info("Audio generated successfully: %d bytes", len(audio_bytes))
            return audio_bytes

        except Exception as e:
            logger.error("Audio generation failed: %s", str(e))
            raise AudioGenerationError(f"Failed to generate audio: {str(e)}") from e

    def save_audio(
        self,
        text: str,
        output_path: Path,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Tuple[Path, float]:
        """Generate audio and save to file.

        Args:
            text: Text to convert to speech
            output_path: Where to save the audio file
            model: TTS model override
            voice: Voice override
            speed: Speech speed (0.25 to 4.0)

        Returns:
            Tuple of (Path to saved audio file, actual duration in seconds)
        """
        audio_bytes = self.generate_audio_bytes(
            text=text,
            model=model,
            voice=voice,
            speed=speed,
        )

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save audio file
        output_path.write_bytes(audio_bytes)
        logger.info("Audio saved to %s", output_path)

        # Calculate actual audio duration
        if PYDUB_AVAILABLE:
            try:
                audio = AudioSegment.from_mp3(output_path)
                duration_seconds = len(audio) / 1000.0  # pydub returns milliseconds
                logger.info("Audio duration: %.2f seconds", duration_seconds)
            except Exception as e:
                logger.warning("Could not determine audio duration with pydub: %s", str(e))
                # Estimate duration based on text length (rough approximation)
                duration_seconds = len(text.split()) / 2.5  # ~2.5 words per second
        else:
            logger.warning("pydub not available, estimating audio duration")
            # Estimate duration based on text length (rough approximation)
            duration_seconds = len(text.split()) / 2.5  # ~2.5 words per second

        return output_path, duration_seconds

    def generate_scene_audio(
        self,
        project_dir: Path,
        scene_number: int,
        narration: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Tuple[Path, float]:
        """Generate and save audio for a specific scene.

        Args:
            project_dir: Project directory
            scene_number: Scene number
            narration: Scene narration text
            model: TTS model override
            voice: Voice override
            speed: Speech speed

        Returns:
            Tuple of (Path to saved audio file, actual duration in seconds)
        """
        audio_dir = ensure_directory(project_dir / "audio")
        audio_path = audio_dir / f"scene_{scene_number:02d}.mp3"

        return self.save_audio(
            text=narration,
            output_path=audio_path,
            model=model,
            voice=voice,
            speed=speed,
        )

    def generate_shot_audio(
        self,
        project_dir: Path,
        scene_number: int,
        shot_number: int,
        narration: str,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> Tuple[Path, float]:
        """Generate and save audio for a specific shot.

        Args:
            project_dir: Project directory
            scene_number: Scene number
            shot_number: Shot number
            narration: Shot narration text
            model: TTS model override
            voice: Voice override
            speed: Speech speed

        Returns:
            Tuple of (Path to saved audio file, actual duration in seconds)
        """
        scene_dir = project_dir / "audio" / f"scene_{scene_number:02d}"
        ensure_directory(scene_dir)
        audio_path = scene_dir / f"shot_{shot_number:02d}.mp3"

        return self.save_audio(
            text=narration,
            output_path=audio_path,
            model=model,
            voice=voice,
            speed=speed,
        )
