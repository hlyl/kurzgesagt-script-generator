"""Image generation utilities."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from ..config import settings
from ..utils import get_logger
from ..utils import ensure_directory

logger = get_logger("image_generator")


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

    def generate_image_bytes(
        self,
        prompt: str,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        style_context: Optional[str] = None,
    ) -> bytes:
        """Generate an image from a prompt and return bytes."""
        if style_context:
            prompt = f"{prompt}\n\nStyle guide: {style_context}"
        logger.debug("Image generation prompt: %s", prompt)
        model_name = model or self.model
        aspect = aspect_ratio or settings.gemini_image_aspect_ratio
        image_size = resolution or settings.gemini_image_resolution
        logger.info(
            "Generating image model=%s aspect=%s size=%s",
            model_name,
            aspect,
            image_size,
        )
        response = self.client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect,
                    image_size=image_size,
                ),
            ),
        )

        for part in response.parts:
            inline = getattr(part, "inline_data", None)
            if inline is not None:
                data = getattr(inline, "data", None)
                if isinstance(data, (bytes, bytearray)):
                    return bytes(data)
                image = part.as_image()
                return self._image_to_bytes(image)

        logger.error("Gemini response missing image data")
        raise ImageGenerationError("Gemini response missing image data.")

    @staticmethod
    def _image_to_bytes(image: Image.Image) -> bytes:
        buffer = io.BytesIO()
        try:
            image.save(buffer, format="PNG")
        except TypeError:
            try:
                image.save(buffer)
            except Exception as exc:  # pragma: no cover - defensive fallback
                raise ImageGenerationError(
                    "Failed to serialize image output."
                ) from exc
        return buffer.getvalue()

    def save_shot_image(
        self,
        project_dir: Path,
        scene_number: int,
        shot_number: int,
        prompt: str,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        style_context: Optional[str] = None,
    ) -> Path:
        """Generate and save a shot image under the project directory."""
        image_bytes = self.generate_image_bytes(
            prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            style_context=style_context,
        )
        scene_dir = project_dir / "images" / f"scene_{scene_number:02d}"
        ensure_directory(scene_dir)
        image_path = scene_dir / f"shot_{shot_number:02d}.png"
        image_path.write_bytes(image_bytes)
        return image_path
