"""Project configuration data model."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from .enums import (
    Aesthetic,
    AspectRatio,
    ColorPalette,
    ImageAspectRatio,
    ImageResolution,
    LineWork,
    ModelType,
    MotionPacing,
    ShotComplexity,
)
from .scene import Scene


class StyleGuide(BaseModel):
    """Visual style configuration."""

    aesthetic: Aesthetic = Field(
        default=Aesthetic.KURZGESAGT, description="Overall aesthetic"
    )
    color_palette: ColorPalette = Field(default=ColorPalette.VIBRANT)
    line_work: LineWork = Field(default=LineWork.MINIMAL_OUTLINES)
    gradients: str = Field(default="soft", description="Gradient style")
    motion_pacing: MotionPacing = Field(default=MotionPacing.SMOOTH)
    texture: str = Field(default="flat", description="Texture style")

    @field_validator("aesthetic", mode="before")
    @classmethod
    def coerce_aesthetic(cls, value):
        if isinstance(value, Aesthetic):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower().replace(" ", "_")
            if normalized == "kurzgesagt-inspired":
                normalized = "kurzgesagt"
            for item in Aesthetic:
                if item.value == normalized:
                    return item
        return Aesthetic.KURZGESAGT


class CharacterConfig(BaseModel):
    """Character and figure configuration."""

    use_named_characters: bool = Field(
        default=False, description="Use named characters"
    )
    avoid_closeups: bool = Field(default=True, description="Avoid facial close-ups")
    style: str = Field(default="abstract_icons", description="Character style")
    detail_level: str = Field(default="simple_shapes", description="Level of detail")


class Environment(BaseModel):
    """Environment/location definition."""

    name: str = Field(..., min_length=1)
    mood: str = Field(..., min_length=1)
    props: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class TechnicalSpecs(BaseModel):
    """Technical production specifications."""

    aspect_ratio: AspectRatio = Field(default=AspectRatio.RATIO_3_2)
    model: ModelType = Field(default=ModelType.VEO_3_2)
    shot_complexity: ShotComplexity = Field(default=ShotComplexity.NESTED)
    avg_shot_duration: str = Field(
        default="5-8", description="Average shot duration range"
    )
    text_on_screen: bool = Field(default=False, description="Include text overlays")
    image_model: str = Field(default="gemini-2.5-flash-image")
    image_aspect_ratio: ImageAspectRatio = Field(
        default=ImageAspectRatio.RATIO_1_1
    )
    image_resolution: ImageResolution = Field(default=ImageResolution.K1)


class ProjectMetadata(BaseModel):
    """Project metadata."""

    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    author: Optional[str] = None


class ProjectConfig(BaseModel):
    """Complete project configuration."""

    metadata: ProjectMetadata
    style: StyleGuide = Field(default_factory=StyleGuide)
    characters: CharacterConfig = Field(default_factory=CharacterConfig)
    technical: TechnicalSpecs = Field(default_factory=TechnicalSpecs)
    environments: List[Environment] = Field(default_factory=list)
    voice_over_script: str = Field(default="", description="Raw voice-over script")
    scenes: List[Scene] = Field(default_factory=list, description="Generated scenes")

    @property
    def total_duration(self) -> int:
        """Calculate total video duration."""
        return sum(scene.duration for scene in self.scenes)

    @property
    def scene_count(self) -> int:
        """Get number of scenes."""
        return len(self.scenes)

    @property
    def shot_count(self) -> int:
        """Get total number of shots."""
        return sum(scene.shot_count for scene in self.scenes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML export."""
        return self.model_dump(mode="json", exclude_none=True)

    def to_yaml(self, path: Path) -> None:
        """Export configuration to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.to_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    @classmethod
    def from_yaml(cls, path: Path) -> "ProjectConfig":
        """Load configuration from YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    @classmethod
    def create_new(cls, title: str, author: Optional[str] = None) -> "ProjectConfig":
        """Create a new project with defaults."""
        return cls(metadata=ProjectMetadata(title=title, author=author))
