"""Tests for model-specific prompt optimization."""

import pytest

from src.kurzgesagt.core.prompt_optimizer import PromptOptimizer
from src.kurzgesagt.models import ModelType, Shot


@pytest.fixture
def sample_shot():
    """Create a sample shot for testing."""
    return Shot(
        number=1,
        image_prompt="A beautiful landscape",
        video_prompt="Camera slowly pans across the scene",
        description="Opening shot of the video",
        key_elements=["mountains", "trees", "sky"],
        duration=5,
        narration="Welcome to the mountains"
    )


class TestPromptOptimizerInit:
    """Test PromptOptimizer initialization."""

    def test_init(self):
        """Test optimizer initialization."""
        optimizer = PromptOptimizer()

        assert optimizer.strategies is not None
        assert ModelType.VEO_3_2 in optimizer.strategies
        assert ModelType.KLING_2_5 in optimizer.strategies
        assert ModelType.SORA_2 in optimizer.strategies
        assert ModelType.RUNWAY_GEN4 in optimizer.strategies
        assert ModelType.GROK_IMAGINE in optimizer.strategies


class TestOptimizeShot:
    """Test shot optimization routing."""

    def test_optimize_shot_veo(self, sample_shot):
        """Test optimization routes to correct strategy for Veo."""
        optimizer = PromptOptimizer()
        result = optimizer.optimize_shot(sample_shot, ModelType.VEO_3_2)

        assert result is not None
        assert isinstance(result, Shot)

    def test_optimize_shot_kling(self, sample_shot):
        """Test optimization routes to correct strategy for Kling."""
        optimizer = PromptOptimizer()
        result = optimizer.optimize_shot(sample_shot, ModelType.KLING_2_5)

        assert result is not None
        assert isinstance(result, Shot)

    def test_optimize_shot_sora(self, sample_shot):
        """Test optimization routes to correct strategy for Sora."""
        optimizer = PromptOptimizer()
        result = optimizer.optimize_shot(sample_shot, ModelType.SORA_2)

        assert result is not None
        assert isinstance(result, Shot)

    def test_optimize_shot_runway(self, sample_shot):
        """Test optimization routes to correct strategy for Runway."""
        optimizer = PromptOptimizer()
        result = optimizer.optimize_shot(sample_shot, ModelType.RUNWAY_GEN4)

        assert result is not None
        assert isinstance(result, Shot)

    def test_optimize_shot_grok(self, sample_shot):
        """Test optimization routes to correct strategy for Grok."""
        optimizer = PromptOptimizer()
        result = optimizer.optimize_shot(sample_shot, ModelType.GROK_IMAGINE)

        assert result is not None
        assert isinstance(result, Shot)


class TestOptimizeForVeo:
    """Test Veo-specific optimization."""

    def test_veo_adds_shot_type_when_missing(self):
        """Test Veo adds shot type description when missing."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A landscape",
            video_prompt="Camera moves",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.VEO_3_2)

        assert "Wide shot" in result.image_prompt

    def test_veo_preserves_existing_shot_type(self):
        """Test Veo doesn't duplicate shot type."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="Close-up shot of a flower",
            video_prompt="Camera moves slowly",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.VEO_3_2)

        # Should not add "Wide shot" since "shot" is already present
        assert result.image_prompt == "Close-up shot of a flower"

    def test_veo_adds_smooth_motion_when_missing(self):
        """Test Veo adds smooth motion description."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A landscape",
            video_prompt="Camera pans left",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.VEO_3_2)

        assert "smooth and intentional" in result.video_prompt

    def test_veo_preserves_existing_smooth_keyword(self):
        """Test Veo doesn't duplicate smooth keyword."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A landscape",
            video_prompt="Smooth camera pan across scene",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.VEO_3_2)

        # Should not modify video_prompt since "smooth" is already there
        assert result.video_prompt == "Smooth camera pan across scene"


class TestOptimizeForKling:
    """Test Kling-specific optimization."""

    def test_kling_adds_motion_precision(self):
        """Test Kling adds motion precision keywords."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A robot",
            video_prompt="Robot moves forward",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.KLING_2_5)

        assert "controlled and precise" in result.video_prompt

    def test_kling_preserves_existing_precision_keywords(self):
        """Test Kling doesn't duplicate precision keywords."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A robot",
            video_prompt="Precise robotic movements with fluid motion",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.KLING_2_5)

        # Should not modify since "precise" and "fluid" are already present
        assert result.video_prompt == "Precise robotic movements with fluid motion"


class TestOptimizeForSora:
    """Test Sora-specific optimization."""

    def test_sora_adds_intent_from_description(self):
        """Test Sora adds intent from description."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A sunset",
            video_prompt="Colors shift gradually",
            description="Peaceful evening scene",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.SORA_2)

        assert "Intent: Peaceful evening scene" in result.video_prompt

    def test_sora_handles_missing_description(self):
        """Test Sora handles shots with minimal description."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A sunset",
            video_prompt="Colors shift",
            description="x",  # Minimal description (not empty due to Pydantic validation)
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.SORA_2)

        # Should add Intent with minimal description
        assert "Intent: x" in result.video_prompt


class TestOptimizeForRunway:
    """Test Runway-specific optimization."""

    def test_runway_adds_camera_prefix(self):
        """Test Runway adds camera choreography."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A cityscape",
            video_prompt="slowly rises above buildings",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.RUNWAY_GEN4)

        assert "The camera" in result.video_prompt
        assert "slowly rises above buildings" in result.video_prompt

    def test_runway_preserves_existing_camera_terms(self):
        """Test Runway doesn't modify if camera terms present."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A cityscape",
            video_prompt="Camera pans left across the scene",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.RUNWAY_GEN4)

        # Should not modify since "Camera" is already present
        assert result.video_prompt == "Camera pans left across the scene"


class TestOptimizeForGrok:
    """Test Grok-specific optimization."""

    def test_grok_truncates_long_prompts(self):
        """Test Grok truncates prompts over 200 characters."""
        optimizer = PromptOptimizer()

        long_prompt = "x" * 250  # 250 character prompt

        shot = Shot(
            number=1,
            image_prompt="A scene",
            video_prompt=long_prompt,
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.GROK_IMAGINE)

        assert len(result.video_prompt) == 200
        assert result.video_prompt.endswith("...")

    def test_grok_preserves_short_prompts(self):
        """Test Grok doesn't modify short prompts."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="A scene",
            video_prompt="Short prompt",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.GROK_IMAGINE)

        assert result.video_prompt == "Short prompt"

    def test_grok_preserves_exactly_200_chars(self):
        """Test Grok handles exactly 200 character prompts."""
        optimizer = PromptOptimizer()

        exact_prompt = "x" * 200

        shot = Shot(
            number=1,
            image_prompt="A scene",
            video_prompt=exact_prompt,
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        result = optimizer.optimize_shot(shot, ModelType.GROK_IMAGINE)

        assert result.video_prompt == exact_prompt


class TestGenericOptimization:
    """Test generic optimization for unknown models."""

    def test_generic_optimization_returns_unchanged_shot(self):
        """Test generic optimization returns shot unchanged."""
        optimizer = PromptOptimizer()
        shot = Shot(
            number=1,
            image_prompt="Original image prompt",
            video_prompt="Original video prompt",
            description="Test description",
            key_elements=[],
            duration=5,
            narration="Test"
        )

        # Test with a model not in strategies (should use generic)
        result = optimizer._generic_optimization(shot)

        assert result.image_prompt == "Original image prompt"
        assert result.video_prompt == "Original video prompt"
