"""Image generation utilities."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from google import genai
from PIL import Image

from ..config import settings
from ..utils import ensure_directory


class ImageGenerationError(RuntimeError):
    """Raised when image generation fails."""


class ImageGenerator:
    """Generate images from prompts and save them to disk."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        size: Optional[str] = None,
    ) -> None:
        resolved_key = api_key or settings.gemini_api_key
        if not resolved_key or resolved_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY must be set for image generation.")
        self.client = genai.Client(api_key=resolved_key)
        self.model = model or settings.gemini_image_model
        self.size = size or settings.gemini_image_size

    def generate_image_bytes(self, prompt: str) -> bytes:
        """Generate an image from a prompt and return bytes."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt],
        )

        for part in response.parts:
            if getattr(part, "inline_data", None) is not None:
                image = part.as_image()
                return self._image_to_bytes(image)

        raise ImageGenerationError("Gemini response missing image data.")

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def save_shot_image(
        self,
        project_dir: Path,
        scene_number: int,
        shot_number: int,
        prompt: str,
    ) -> Path:
        """Generate and save a shot image under the project directory."""
        image_bytes = self.generate_image_bytes(prompt)
        scene_dir = project_dir / "images" / f"scene_{scene_number:02d}"
        ensure_directory(scene_dir)
        image_path = scene_dir / f"shot_{shot_number:02d}.png"
        image_path.write_bytes(image_bytes)
        return image_path
