"""Video generation from images using Google Veo 3.1."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import requests
from google import genai
from google.genai import types

from ..utils import get_logger

logger = get_logger("video_generator")


class VideoGenerationError(RuntimeError):
    """Raised when video generation fails."""


@dataclass
class VideoResult:
    """Result of video generation with optional manual download URI."""
    video_bytes: Optional[bytes] = None
    uri: Optional[str] = None
    requires_manual_download: bool = False
    
    @property
    def success(self) -> bool:
        """Check if video bytes were successfully obtained."""
        return self.video_bytes is not None
    
    @property
    def has_fallback_uri(self) -> bool:
        """Check if a fallback URI is available for manual download."""
        return self.uri is not None and self.requires_manual_download


class VideoGenerator:
    """Generate animated videos from images using Google Veo 3.1.

    Uses image-to-video generation with 9:16 aspect ratio and 8-second duration.
    """

    def __init__(self, api_key: Optional[str] = None, drive_uploader=None, keep_local_copy: bool = True):
        """Initialize with Gemini API key and optional Google Drive uploader.

        Args:
            api_key: Gemini API key (same as image generation)
            drive_uploader: Optional GoogleDriveUploader instance for auto-upload
            keep_local_copy: Whether to keep local copy after Drive upload (default: True)

        Raises:
            VideoGenerationError: If API key is not provided
        """
        if not api_key:
            raise VideoGenerationError("Gemini API key is required")

        self.client = genai.Client(api_key=api_key)
        self.drive_uploader = drive_uploader
        self.keep_local_copy = keep_local_copy
        logger.info("VideoGenerator initialized with Gemini API")

        if self.drive_uploader and self.drive_uploader.is_configured():
            logger.info("Google Drive uploader is configured and ready")
            if not self.keep_local_copy:
                logger.info("Local copies will be deleted after Drive upload")

    def generate_video_from_image(
        self,
        image_path: Path,
        video_prompt: str,
        key_elements: List[str],
        style_context: str,
        duration: int = 8,
        aspect_ratio: str = "9:16"
    ) -> VideoResult:
        """Generate video from image using Veo 3.1.

        Args:
            image_path: Path to PNG image (first frame)
            video_prompt: Base prompt for video animation
            key_elements: List of elements to animate
            style_context: Aesthetic description from config.style
            duration: Video duration in seconds (default: 8, Veo 3.1 limit)
            aspect_ratio: Output aspect ratio (default: 9:16)

        Returns:
            VideoResult: Contains video bytes or URI for manual download

        Raises:
            VideoGenerationError: If generation fails (not download)
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
                config=types.GenerateVideosConfig(
                    aspectRatio="9:16",
                    durationSeconds=8
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
                # Pass the operation object itself, not operation.name
                operation = self.client.operations.get(operation)
            except Exception as e:
                raise VideoGenerationError(f"Failed to poll operation status: {e}") from e

            poll_count += 1
            if poll_count % 6 == 0:  # Log every minute
                logger.info(f"Still generating... ({poll_count * 10}s elapsed)")

        # Extract video bytes from result
        if not operation.response:
            raise VideoGenerationError("Operation completed but no video data returned")

        try:
            # Response contains a list of generated videos
            if not operation.response.generated_videos:
                raise VideoGenerationError("No videos generated in response")

            # Get the first generated video (we only requested one)
            generated_video = operation.response.generated_videos[0]
            video = generated_video.video

            # Extract bytes from Video object
            if hasattr(video, 'video_bytes') and video.video_bytes:
                video_data = video.video_bytes
                logger.info(f"Video generated successfully ({len(video_data)} bytes)")
                return VideoResult(video_bytes=video_data)
            
            elif hasattr(video, 'uri') and video.uri:
                # Download video from URI (signed URL from Google Cloud Storage)
                logger.info(f"Downloading video from URI...")
                try:
                    # Use requests for better error handling and redirect support
                    response = requests.get(video.uri, timeout=300)
                    response.raise_for_status()
                    video_data = response.content
                    logger.info(f"Video downloaded successfully ({len(video_data)} bytes)")
                    return VideoResult(video_bytes=video_data)
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403:
                        # 403 Forbidden - video generated but can't auto-download
                        logger.warning(
                            f"Video generated successfully but automatic download failed (HTTP 403). "
                            f"Returning URI for manual download."
                        )
                        return VideoResult(
                            uri=video.uri,
                            requires_manual_download=True
                        )
                    else:
                        # Other HTTP errors - try to return URI as fallback
                        logger.error(
                            f"HTTP {e.response.status_code} error downloading video. "
                            f"Returning URI for manual download."
                        )
                        return VideoResult(
                            uri=video.uri,
                            requires_manual_download=True
                        )
                        
                except requests.exceptions.Timeout:
                    logger.warning("Download timed out. Returning URI for manual download.")
                    return VideoResult(
                        uri=video.uri,
                        requires_manual_download=True
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to download video: {e}. Returning URI for manual download.")
                    return VideoResult(
                        uri=video.uri,
                        requires_manual_download=True
                    )
            else:
                raise VideoGenerationError("Video object has no video_bytes or uri")

        except VideoGenerationError:
            raise
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
    ) -> Union[Path, str, dict]:
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
            Path: Saved video file path if successful
            str: Download URI if automatic download failed
            dict: Contains 'local_path' and 'drive_file_id' if uploaded to Drive

        Raises:
            VideoGenerationError: If generation fails
        """
        # Generate video
        result = self.generate_video_from_image(
            image_path=image_path,
            video_prompt=video_prompt,
            key_elements=key_elements,
            style_context=style_context,
            duration=8,
            aspect_ratio="9:16"
        )

        # Check if we got video bytes
        if result.success:
            # Save to project directory
            video_dir = project_dir / "videos" / f"scene_{scene_number:02d}"
            video_dir.mkdir(parents=True, exist_ok=True)

            video_path = video_dir / f"shot_{shot_number:02d}.mp4"

            try:
                video_path.write_bytes(result.video_bytes)
                logger.info(f"Saved video to {video_path}")

                # Upload to Google Drive if configured
                if self.drive_uploader and self.drive_uploader.is_configured():
                    try:
                        folder_name = f"scene_{scene_number:02d}"
                        drive_file_id = self.drive_uploader.upload_video(
                            video_path=video_path,
                            folder_name=folder_name,
                            file_name=f"shot_{shot_number:02d}.mp4"
                        )

                        logger.info(f"Uploaded to Google Drive (ID: {drive_file_id})")

                        drive_result = {
                            'drive_file_id': drive_file_id,
                            'drive_link': self.drive_uploader.get_file_link(drive_file_id)
                        }

                        # Delete local file if keep_local_copy is False
                        if not self.keep_local_copy:
                            try:
                                video_path.unlink()
                                logger.info(f"Deleted local copy: {video_path}")
                            except Exception as e:
                                logger.warning(f"Failed to delete local file: {e}")
                        else:
                            # Include local path only if keeping it
                            drive_result['local_path'] = video_path

                        return drive_result
                    except Exception as e:
                        logger.warning(f"Failed to upload to Google Drive: {e}")
                        # Continue and return local path only

                return video_path

            except Exception as e:
                raise VideoGenerationError(f"Failed to save video: {e}") from e

        elif result.has_fallback_uri:
            # Return URI for manual download
            logger.info(
                f"Video generated but requires manual download. "
                f"URI available for scene {scene_number}, shot {shot_number}"
            )
            return result.uri

        else:
            raise VideoGenerationError(
                "Video generation completed but no video data or URI available"
            )