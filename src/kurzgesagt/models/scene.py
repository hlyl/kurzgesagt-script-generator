"""Scene and shot data models."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Shot(BaseModel):
    """Represents a single shot in a scene."""

    number: int = Field(..., ge=1, description="Shot number (1-indexed)")
    narration: str = Field(
        ..., min_length=1, description="Voice-over narration for this shot"
    )
    duration: float = Field(..., ge=0.1, le=60.0, description="Shot duration in seconds (actual audio duration)")
    description: str = Field(
        ..., min_length=1, description="What this shot accomplishes"
    )
    key_elements: List[str] = Field(
        default_factory=list, description="Key visual elements"
    )
    image_prompt: str = Field(..., min_length=1, description="Text-to-image prompt")
    video_prompt: str = Field(..., min_length=1, description="Image-to-video prompt")
    is_nested: bool = Field(
        default=False, description="Whether shot contains nested camera moves"
    )
    transition_note: Optional[str] = Field(
        None, description="How to transition to next shot"
    )
    transition_duration: float = Field(
        default=0.5, ge=0.0, le=5.0, description="Transition duration to next shot in seconds"
    )

    @field_validator("key_elements")
    @classmethod
    def validate_key_elements(cls, v: List[str]) -> List[str]:
        """Ensure key elements are not empty strings."""
        return [elem.strip() for elem in v if elem.strip()]


class Scene(BaseModel):
    """Represents a scene (collection of related shots)."""

    number: int = Field(..., ge=1, description="Scene number (1-indexed)")
    title: str = Field(..., min_length=1, description="Scene title (uppercase)")
    purpose: str = Field(..., min_length=1, description="Narrative goal of this scene")
    duration: float = Field(..., ge=0.1, description="Total scene duration in seconds (actual)")
    shots: List[Shot] = Field(default_factory=list, description="Shots in this scene")
    transition_duration: float = Field(
        default=1.0, ge=0.0, le=5.0, description="Transition duration to next scene in seconds"
    )

    @field_validator("title")
    @classmethod
    def title_uppercase(cls, v: str) -> str:
        """Ensure title is uppercase."""
        return v.upper()

    @property
    def shot_count(self) -> int:
        """Get number of shots in this scene."""
        return len(self.shots)

    def add_shot(self, shot: Shot) -> None:
        """Add a shot to this scene."""
        self.shots.append(shot)

    def calculate_duration(self) -> float:
        """Calculate total duration from shots including their transitions."""
        if not self.shots:
            return 0.0
        # Sum all shot durations + their transition durations except the last shot's transition
        total = sum(shot.duration + shot.transition_duration for shot in self.shots[:-1])
        # Add last shot duration without transition
        total += self.shots[-1].duration
        return total
