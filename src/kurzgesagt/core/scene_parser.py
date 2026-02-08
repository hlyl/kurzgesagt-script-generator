"""Scene parsing using LLM providers."""

import json
from typing import Any, Dict, List, Optional, cast
from pydantic import ValidationError as PydanticValidationError

from ..models import Scene, Shot, StyleGuide
from .providers import ProviderConfigError, SceneParsingProvider, get_scene_provider


class SceneParsingError(Exception):
    """Raised when scene parsing fails."""

    pass


class SceneParser:
    """Parses voice-over scripts into structured scenes using providers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: Optional[SceneParsingProvider] = None,
        provider_name: Optional[str] = None,
    ):
        """
        Initialize scene parser.

        Args:
            api_key: Anthropic API key (defaults to settings)
        """
        if provider is not None:
            self.provider = provider
        else:
            try:
                self.provider = get_scene_provider(
                    provider_name=provider_name,
                    api_key=api_key,
                )
            except ProviderConfigError as exc:
                raise ValueError(str(exc)) from exc

    def parse_script(
        self,
        voice_over: str,
        style_guide: StyleGuide,
        shot_complexity: str = "nested",
    ) -> List[Scene]:
        """
        Parse voice-over script into scenes and shots.

        Args:
            voice_over: Raw voice-over script
            style_guide: Visual style configuration
            shot_complexity: Shot complexity level

        Returns:
            List of Scene objects

        Raises:
            SceneParsingError: If parsing fails
        """
        try:
            # Build prompt
            prompt = self._build_parsing_prompt(
                voice_over, style_guide, shot_complexity
            )

            response_text = self.provider.complete(prompt)
            scenes_data = self._extract_json(response_text)

            # Convert to Scene objects
            scenes = self._json_to_scenes(scenes_data)

            return scenes

        except RuntimeError as e:
            raise SceneParsingError(str(e)) from e
        except (json.JSONDecodeError, KeyError, PydanticValidationError) as e:
            raise SceneParsingError(f"Failed to parse response: {str(e)}") from e

    def _build_parsing_prompt(
        self,
        voice_over: str,
        style_guide: StyleGuide,
        shot_complexity: str,
    ) -> str:
        """Build the parsing prompt for Claude."""
        lines = [
            (
                "You are an expert video production assistant specializing in "
                "Kurzgesagt-style explainer videos."
            ),
            "",
            (
                "Break this voice-over script into scenes and shots following "
                "these guidelines:"
            ),
            "",
            "STYLE GUIDE:",
            f"- Aesthetic: {style_guide.aesthetic}",
            f"- Color Palette: {style_guide.color_palette.value}",
            f"- Line Work: {style_guide.line_work.value}",
            f"- Motion: {style_guide.motion_pacing.value}",
            "",
            f"SHOT COMPLEXITY: {shot_complexity}",
            "- If \"simple\": 1 camera movement per shot",
            "- If \"nested\": 2-3 camera movements per shot",
            "- If \"hybrid\": Mix of simple and nested",
            "",
            "VOICE-OVER SCRIPT:",
            voice_over,
            "",
            (
                "Return ONLY a JSON object with this exact structure (no "
                "markdown, no explanations):"
            ),
            "{",
            '  "scenes": [',
            "    {",
            '      "number": 1,',
            '      "title": "SCENE TITLE IN CAPS",',
            '      "purpose": "What this scene accomplishes narratively",',
            '      "duration": 15,',
            '      "shots": [',
            "        {",
            '          "number": 1,',
            '          "narration": "Exact voice-over text for this shot",',
            '          "duration": 5,',
            '          "description": "What this shot accomplishes visually",',
            '          "key_elements": ["element1", "element2"],',
            (
                "          \"image_prompt\": \"Detailed Kurzgesagt-style image "
                "prompt with composition, colors, objects, mood. Always end "
                "with 'Flat 2D illustration, Kurzgesagt style, clean vector "
                "shapes, soft gradients'\","  # noqa: E501
            ),
            (
                "          \"video_prompt\": \"Detailed motion description: "
                "camera movement, object animation, transitions. Be specific "
                "about timing and progression.\","  # noqa: E501
            ),
            '          "is_nested": true,',
            '          "transition_note": "How this connects to next shot"',
            "        }",
            "      ]",
            "    }",
            "  ]",
            "}",
            "",
            "IMPORTANT:",
            "- Match narration timing to shot durations",
            "- Keep image prompts focused on composition and style",
            "- Keep video prompts focused on motion and camera work",
            "- For nested shots, describe 2-3 distinct visual beats",
            "- Use Kurzgesagt visual language: flat, iconic, metaphorical",
        ]
        return "\n".join(lines)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Claude's response, handling markdown code blocks."""
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            # Find the JSON content between ``` markers
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        return cast(Dict[str, Any], json.loads(text))

    def _json_to_scenes(self, data: dict) -> List[Scene]:
        """Convert JSON data to Scene objects."""
        scenes = []

        for scene_data in data.get("scenes", []):
            # Parse shots
            shots = []
            for shot_data in scene_data.get("shots", []):
                shot = Shot(**shot_data)
                shots.append(shot)

            # Create scene
            scene = Scene(
                number=scene_data["number"],
                title=scene_data["title"],
                purpose=scene_data["purpose"],
                duration=scene_data["duration"],
                shots=shots,
            )
            scenes.append(scene)

        return scenes
