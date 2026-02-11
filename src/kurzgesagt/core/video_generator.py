"""Video generation from images using Google Veo 3.1."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types

from ..utils import get_logger

logger = get_logger("video_generator")


class VideoGenerationError(RuntimeError):
    """Raised when video generation fails."""


class VideoGenerator:
    """Generate animated videos from images using Google Veo 3.1.

    Uses image-to-video generation with 9:16 aspect ratio and 8-second duration.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key.

        Args:
            api_key: Gemini API key (same as image generation)

        Raises:
            VideoGenerationError: If API key is not provided
        """
        if not api_key:
            raise VideoGenerationError("Gemini API key is required")

        self.client = genai.Client(api_key=api_key)
        logger.info("VideoGenerator initialized with Gemini API")

    def generate_video_from_image(
        self,
        image_path: Path,
        video_prompt: str,
        key_elements: List[str],
        style_context: str,
        duration: int = 8,
        aspect_ratio: str = "9:16"
    ) -> bytes:
        """Generate video from image using Veo 3.1.

        Args:
            image_path: Path to PNG image (first frame)
            video_prompt: Base prompt for video animation
            key_elements: List of elements to animate
            style_context: Aesthetic description from config.style
            duration: Video duration in seconds (default: 8, Veo 3.1 limit)
            aspect_ratio: Output aspect ratio (default: 9:16)

        Returns:
            bytes: MP4 video data

        Raises:
            VideoGenerationError: If generation fails
        """
        logger.info(f"Generating video from {image_path}")

        # Read image as bytes
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
        except Exception as e:
            raise VideoGenerationError(f"Failed to read image: {e}") from e

        # Construct enhanced prompt
        elements_str = ", ".join(key_elements) if key_elements else "all elements"
        enhanced_prompt = self._build_video_prompt(
            video_prompt, elements_str, style_context
        )

        logger.debug(f"Video prompt: {enhanced_prompt[:200]}...")

        # Start video generation operation
        try:
            operation = self.client.models.generate_videos(
                model="veo-3.1-generate-preview",
                prompt=enhanced_prompt,
                image=types.Image(
                    image_bytes=image_bytes,
                    mime_type="image/png"
                ),
                config=types.VideoConfig(
                    aspect_ratio="9:16",
                    duration_seconds=8
                )
            )
        except Exception as e:
            raise VideoGenerationError(f"Failed to start video generation: {e}") from e

        # Poll for completion
        logger.info("Polling for video generation completion...")
        poll_count = 0
        max_polls = 60  # 10 minutes max (10s intervals)

        while not operation.done:
            if poll_count >= max_polls:
                raise VideoGenerationError("Video generation timed out after 10 minutes")

            time.sleep(10)  # Wait 10 seconds between polls

            try:
                operation = self.client.operations.get(operation.name)
            except Exception as e:
                raise VideoGenerationError(f"Failed to poll operation status: {e}") from e

            poll_count += 1
            if poll_count % 6 == 0:  # Log every minute
                logger.info(f"Still generating... ({poll_count * 10}s elapsed)")

        # Extract video bytes from result
        if not operation.response:
            raise VideoGenerationError("Operation completed but no video data returned")

        try:
            video_data = operation.response.video
            logger.info(f"Video generated successfully ({len(video_data)} bytes)")
            return video_data
        except Exception as e:
            raise VideoGenerationError(f"Failed to extract video data: {e}") from e

    def _build_video_prompt(
        self,
        base_prompt: str,
        key_elements: str,
        style_context: str
    ) -> str:
        """Build enhanced video prompt with style and animation guidance.

        Args:
            base_prompt: Original video_prompt from shot
            key_elements: Comma-separated key elements to animate
            style_context: Aesthetic description with animation specs

        Returns:
            Enhanced prompt string
        """
        prompt_parts = [
            base_prompt,
            f"\nAnimate these key elements: {key_elements}",
            f"\nStyle and animation details:",
            style_context[:500],  # Limit style context to 500 chars
            "\nCamera movement: Smooth cinematic motion with subtle zoom and parallax effects.",
            "Maintain visual consistency with the starting image while adding dynamic movement.",
            "Duration: 8 seconds with consistent pacing throughout."
        ]

        return "\n".join(prompt_parts)

    def save_shot_video(
        self,
        project_dir: Path,
        scene_number: int,
        shot_number: int,
        image_path: Path,
        video_prompt: str,
        key_elements: List[str],
        style_context: str
    ) -> Path:
        """Generate and save video for a specific shot.

        Args:
            project_dir: Project root directory
            scene_number: Scene number (1-indexed)
            shot_number: Shot number (1-indexed)
            image_path: Path to source image
            video_prompt: Video animation prompt
            key_elements: Elements to animate
            style_context: Style description

        Returns:
            Path: Saved video file path

        Raises:
            VideoGenerationError: If generation or save fails
        """
        # Generate video
        video_bytes = self.generate_video_from_image(
            image_path=image_path,
            video_prompt=video_prompt,
            key_elements=key_elements,
            style_context=style_context,
            duration=8,
            aspect_ratio="9:16"
        )

        # Save to project directory
        video_dir = project_dir / "videos" / f"scene_{scene_number:02d}"
        video_dir.mkdir(parents=True, exist_ok=True)

        video_path = video_dir / f"shot_{shot_number:02d}.mp4"

        try:
            video_path.write_bytes(video_bytes)
            logger.info(f"Saved video to {video_path}")
            return video_path
        except Exception as e:
            raise VideoGenerationError(f"Failed to save video: {e}") from e
