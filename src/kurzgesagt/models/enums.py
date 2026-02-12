"""Enumeration types for the application."""

from enum import Enum


class AspectRatio(str, Enum):
    """Supported video aspect ratios."""
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_3_2 = "3:2"
    RATIO_1_1 = "1:1"
    RATIO_21_9 = "21:9"


class ImageAspectRatio(str, Enum):
    """Supported image aspect ratios."""

    RATIO_1_1 = "1:1"
    RATIO_2_3 = "2:3"
    RATIO_3_2 = "3:2"
    RATIO_3_4 = "3:4"
    RATIO_4_3 = "4:3"
    RATIO_4_5 = "4:5"
    RATIO_5_4 = "5:4"
    RATIO_9_16 = "9:16"
    RATIO_16_9 = "16:9"
    RATIO_21_9 = "21:9"


class ImageResolution(str, Enum):
    """Supported image resolution presets."""

    K1 = "1K"
    K2 = "2K"
    K4 = "4K"


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


class Aesthetic(Enum):
    """Aesthetic presets optimized for image-to-video animation workflows.
    
    Note: Color specifications handled separately via color palette parameter.
    """

    # Clean, modern styles
    KURZGESAGT = (
        "modern vector infographic style",
        "Clean vector illustration with thick, consistent black outlines and a friendly, rounded aesthetic. "
        "All shapes feature soft, radiused corners. Smooth gradient fills within objects create subtle "
        "volume and depth without harsh shadows or textures. Flat, orthographic perspective. "
        # Animation-ready specs:
        "Objects isolated on separate layers, clear negative space (20% padding), "
        "distinct foreground/midground/background separation, centered composition "
        "with room for camera pans, simplified icon-like symbols, matte finish, "
        "professional and highly legible layout."
    )

    EDUCATIONAL_MINIMAL = (
        "educational_minimal",
        "Minimalist line art, thin strokes (2-3px), "
        "generous whitespace, clean sans-serif labels, simple diagrams, no shadows, "
        "high contrast text, grid-based layouts, technical drawing style. "
        # Animation-ready specs:
        "Pure white or transparent background for easy extraction, "
        "each diagram element spatially separated (10px minimum), "
        "labels detached from objects (connectable via leader lines in animation), "
        "modular components that can animate independently, "
        "consistent stroke width for smooth morphing, clear bounding boxes"
    )

    # Documentary/presentation styles
    CINEMATIC_DOC = (
        "cinematic_doc",
        "Soft gradient overlays, atmospheric lighting, subtle paper textures, "
        "gentle vignettes, depth through layering, film grain overlay (10% opacity). "
        # Animation-ready specs:
        "Three distinct depth layers (background/subject/foreground), "
        "subject isolated with subtle alpha edge for parallax movement, "
        "vignette on separate layer, grain as overlay, "
        "headroom for vertical camera movement (30% top space), "
        "gradients radial from center for zoom animations"
    )

    CORPORATE_CLEAN = (
        "corporate_clean",
        "Professional business aesthetic, "
        "subtle drop shadows, modern sans-serif typography, polished vector icons, "
        "clean interface elements, organized grid layouts, isometric perspective. "
        # Animation-ready specs:
        "Icons on transparent background with 40px safe area, "
        "drop shadows on separate layer (removable), "
        "grid-aligned elements for slide/fade transitions, "
        "text blocks with clear margins for wipe effects, "
        "consistent icon sizing for sequential reveals, "
        "elements grouped by animation timing (intro/main/outro)"
    )

    # Technical/scientific styles
    BLUEPRINT_TECHNICAL = (
        "blueprint_technical",
        "Technical drawing style, light lines on dark background, "
        "precise measurements and annotations, grid paper overlay, "
        "engineering blueprint aesthetic, monospaced labels, orthographic projections. "
        # Animation-ready specs:
        "Grid as separate background layer, main drawing layer, annotation layer, "
        "line segments separated for progressive drawing animation, "
        "labels positioned outside object bounds for independent fade-in, "
        "measurements detached from dimension lines, "
        "components organized in build order (base to complex)"
    )

    SCIENTIFIC_DIAGRAM = (
        "scientific_diagram",
        "Clean vector illustrations, scientific journal aesthetic, "
        "clear labels with leader lines, categorical color coding, "
        "cutaway views, cross-sections, anatomical precision, neutral backgrounds. "
        # Animation-ready specs:
        "Each anatomical component as isolated object with clean edges, "
        "labels and leader lines on separate layer, "
        "cutaway sections detachable for reveal animations, "
        "color groups separated for sequential highlighting, "
        "arrows/pointers as separate elements for motion paths, "
        "transparent background, high-contrast edges for easy masking"
    )

    # Engaging/creative styles
    HAND_DRAWN_FRIENDLY = (
        "hand_drawn_friendly",
        "Warm hand-drawn illustration, slightly imperfect lines, "
        "watercolor-style fills, textured paper background, "
        "playful annotations with arrows and circles, sketchbook feel. "
        # Animation-ready specs:
        "Paper texture on static background layer, "
        "line art and fills on separate layers for draw-on effect, "
        "annotations isolated for sequential appearance, "
        "elements with matching 'rough edge' style for consistency when animating, "
        "generous spacing for bounce/wiggle animations, "
        "stroke paths drawable (SVG-compatible)"
    )

    INFOGRAPHIC_MODERN = (
        "infographic_modern",
        "Bold data visualization aesthetic, high contrast accent colors against neutral base, "
        "clean iconography, geometric charts and graphs, hierarchy through size and contrast. "
        # Animation-ready specs:
        "Chart elements separated (bars, lines, axes, labels), "
        "data points as individual objects for staggered reveals, "
        "background/foreground contrast for focus effects, "
        "icons with consistent anchor points for entrance animations, "
        "numerical text separate from graphic elements for count-up effects, "
        "modular grid allowing rearrangement"
    )

    RETRO_EDUCATIONAL = (
        "retro_educational",
        "Vintage textbook aesthetic, aged paper texture, "
        "limited color palette with high contrast, "
        "engraving-style illustrations, serif typography, 1960s educational film style. "
        # Animation-ready specs:
        "Paper texture as static base, illustrations as separate layer, "
        "stippled shading as overlay for fade effects, "
        "clear object outlines for rotoscope-style animation, "
        "text frames distinct from illustrations, "
        "aged film scratches/dust on topmost layer, "
        "high contrast for easy alpha extraction"
    )

    # Specialized styles
    CHALKBOARD_LECTURE = (
        "chalkboard_lecture",
        "Light chalk on dark background, "
        "hand-drawn mathematical notation, rough sketch quality, "
        "chalk dust texture, lecture hall aesthetic. "
        # Animation-ready specs:
        "Chalkboard as solid background, each equation/symbol separate, "
        "stroke order preserved for draw-on animation, "
        "chalk dust overlay on separate layer, "
        "eraser marks as alpha mask layer, "
        "progressive complexity (simple to detailed) layout, "
        "elements positioned for revealing sequences"
    )

    FLAT_MOTION_DESIGN = (
        "flat_motion_design",
        "Contemporary flat design, bold geometric shapes, gradient-free solid fills, "
        "sharp edges, overlapping layers, high contrast palette, "
        "simple character designs, 2.5D depth through layering. "
        # Animation-ready specs:
        "Each shape as discrete object with clean paths, "
        "Z-axis depth ordering clear (layer 1, 2, 3...), "
        "shapes designed for morphing (matching vertex counts), "
        "negative space preserved for slide transitions, "
        "character limbs separated at joints for puppet animation, "
        "consistent geometric centers for rotation pivots, "
        "color fills separate from outlines"
    )

    ISOMETRIC_TECH = (
        "isometric_tech",
        "Isometric projection (30° angle), tech startup aesthetic, "
        "gradient color schemes, subtle shadows for depth, "
        "modern SaaS marketing style, floating elements. "
        # Animation-ready specs:
        "Each isometric object isolated with matching perspective, "
        "shadows on separate multiply layer, "
        "floating elements at varied Z-heights for parallax, "
        "connection lines/arrows separate from objects, "
        "consistent isometric grid for object positioning, "
        "gradients directional (top-to-bottom) for uniform lighting in animation, "
        "elements sized for assembly animation sequence"
    )

    # NEW: Optimized specifically for animation workflows
    PARALLAX_LAYERS = (
        "parallax_layers",
        "Multi-depth scene construction, clear foreground/midground/background, "
        "atmospheric perspective (desaturation and blur with distance), "
        "separated elements at varying scales. "
        # Animation-ready specs:
        "Minimum 3 distinct depth layers with 100px depth separation, "
        "foreground elements at 100% opacity/saturation, "
        "midground at 80%, background at 50%, "
        "no layer interdependencies, each layer complete and maskable, "
        "horizon line consistent across layers, "
        "objects decrease 20% size per depth layer, "
        "overlap zones minimal for clean layer separation"
    )

    MORPHABLE_SHAPES = (
        "morphable_shapes",
        "Geometric primitives (circles, squares, triangles), "
        "consistent vertex counts, modular construction, "
        "shape-based composition over textures. "
        # Animation-ready specs:
        "All shapes with matching 8-point vertex structure, "
        "anchor points at geometric centers and cardinal directions, "
        "outlines and fills as separate paths, "
        "shapes arranged in transformation sequence, "
        "consistent scale increments (50%, 100%, 150%), "
        "smooth color transitions within same hue family, "
        "no raster elements (all vector for infinite scaling)"
    )

    SEQUENTIAL_BUILD = (
        "sequential_build",
        "Process diagram aesthetic, numbered steps, directional flow, "
        "logical progression from simple to complex, "
        "modular components that assemble. "
        # Animation-ready specs:
        "Each step as isolated group with internal structure, "
        "connection arrows separate from step elements, "
        "numbered badges on topmost layer, "
        "components arranged left-to-right or top-to-bottom build order, "
        "consistent spacing (120px) for timed reveals, "
        "visual state variations pre-designed (normal/active/complete), "
        "dependency chains clear for cascade animations"
    )


    def __init__(self, value: str, description: str) -> None:
        self._value_ = value
        normalized = description.rstrip()
        if "no text" not in normalized.lower():
            normalized = f"{normalized} No text or lettering in the image."
        self.description = normalized