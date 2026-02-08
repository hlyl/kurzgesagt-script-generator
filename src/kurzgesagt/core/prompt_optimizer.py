"""Model-specific prompt optimization."""

from typing import Dict, Callable
from ..models import ModelType, Shot


class PromptOptimizer:
    """Optimizes prompts for specific AI video models."""
    
    def __init__(self):
        """Initialize optimizer with model-specific strategies."""
        self.strategies: Dict[ModelType, Callable] = {
            ModelType.VEO_3_2: self._optimize_for_veo,
            ModelType.KLING_2_5: self._optimize_for_kling,
            ModelType.SORA_2: self._optimize_for_sora,
            ModelType.RUNWAY_GEN4: self._optimize_for_runway,
            ModelType.GROK_IMAGINE: self._optimize_for_grok,
        }
    
    def optimize_shot(self, shot: Shot, model: ModelType) -> Shot:
        """
        Optimize a shot's prompts for specific model.
        
        Args:
            shot: Shot to optimize
            model: Target model
            
        Returns:
            Shot with optimized prompts
        """
        strategy = self.strategies.get(model, self._generic_optimization)
        return strategy(shot)
    
    def _optimize_for_veo(self, shot: Shot) -> Shot:
        """
        Optimize for Google Veo 3.2.
        
        Veo prefers:
        - Shot type descriptions (wide shot, close-up, etc.)
        - Lighting and mood keywords
        - Camera movement specified clearly
        - Natural pacing cues
        """
        # Enhance image prompt with cinematic language
        if "shot" not in shot.image_prompt.lower():
            shot.image_prompt = f"Wide shot. {shot.image_prompt}"
        
        # Enhance video prompt with pacing
        if "smooth" not in shot.video_prompt.lower():
            shot.video_prompt = f"{shot.video_prompt} The motion is smooth and intentional."
        
        return shot
    
    def _optimize_for_kling(self, shot: Shot) -> Shot:
        """
        Optimize for Kling 2.5.
        
        Kling excels at:
        - Precise motion control language
        - Physics-based descriptions
        - Element-specific animation notes
        """
        # Add motion precision keywords
        motion_keywords = ["precise", "controlled", "fluid"]
        if not any(kw in shot.video_prompt.lower() for kw in motion_keywords):
            shot.video_prompt = f"{shot.video_prompt} Motion is controlled and precise."
        
        return shot
    
    def _optimize_for_sora(self, shot: Shot) -> Shot:
        """
        Optimize for OpenAI Sora 2.
        
        Sora responds to:
        - Intent and mood over mechanics
        - Emotional tone
        - Story-driven language
        """
        # Add mood/intent if missing
        if shot.description:
            shot.video_prompt = f"Intent: {shot.description}. {shot.video_prompt}"
        
        return shot
    
    def _optimize_for_runway(self, shot: Shot) -> Shot:
        """
        Optimize for Runway Gen-4.5.
        
        Runway excels at:
        - Camera choreography
        - Cinematic movement
        - Expressive camera work
        """
        # Emphasize camera movement
        camera_terms = ["camera", "pan", "zoom", "tracking"]
        if not any(term in shot.video_prompt.lower() for term in camera_terms):
            shot.video_prompt = f"The camera {shot.video_prompt.lower()}"
        
        return shot
    
    def _optimize_for_grok(self, shot: Shot) -> Shot:
        """
        Optimize for Grok Imagine.
        
        Grok is fast but benefits from:
        - Concise, clear prompts
        - Simple motion descriptions
        """
        # Keep prompts concise (under 200 chars for video)
        if len(shot.video_prompt) > 200:
            # Simplify while keeping key motion
            shot.video_prompt = shot.video_prompt[:197] + "..."
        
        return shot
    
    def _generic_optimization(self, shot: Shot) -> Shot:
        """Generic optimization for unknown models."""
        return shot