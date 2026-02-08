"""Enumeration types for the application."""

from enum import Enum


class AspectRatio(str, Enum):
    """Supported video aspect ratios."""
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_3_2 = "3:2"
    RATIO_1_1 = "1:1"
    RATIO_21_9 = "21:9"


class ModelType(str, Enum):
    """Supported AI video generation models."""
    VEO_3_2 = "veo_3_2"
    KLING_2_5 = "kling_2_5"
    SORA_2 = "sora_2"
    RUNWAY_GEN4 = "runway_gen4"
    GROK_IMAGINE = "grok_imagine"
    SEEDANCE_1_5 = "seedance_1_5"
    GENERIC = "generic"


class ShotComplexity(str, Enum):
    """Shot structure complexity levels."""
    SIMPLE = "simple"
    NESTED = "nested"
    HYBRID = "hybrid"


class ColorPalette(str, Enum):
    """Color palette options."""
    VIBRANT = "vibrant"
    WARM = "warm"
    COOL = "cool"
    MUTED = "muted"
    PASTEL = "pastel"


class LineWork(str, Enum):
    """Line work styles."""
    MINIMAL_OUTLINES = "minimal_outlines"
    BOLD_STROKES = "bold_strokes"
    NO_OUTLINES = "no_outlines"


class MotionPacing(str, Enum):
    """Motion pacing options."""
    SMOOTH = "smooth"
    ENERGETIC = "energetic"
    CONTEMPLATIVE = "contemplative"
    VARIED = "varied"