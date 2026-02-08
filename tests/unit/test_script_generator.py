"""Unit tests for ScriptGenerator optimization."""


from src.kurzgesagt.core import ScriptGenerator
from src.kurzgesagt.models import ProjectConfig, ProjectMetadata, Scene, Shot


def test_generate_script_applies_prompt_optimization(temp_dir):
    """Ensure prompt optimization is applied before template rendering."""
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    template_path = templates_dir / "script_structure.md.j2"
    template_path.write_text(
        "{{ project.scenes[0].shots[0].image_prompt }}\n"
        "{{ project.scenes[0].shots[0].video_prompt }}",
        encoding="utf-8",
    )

    shot = Shot(
        number=1,
        narration="Test narration",
        duration=5,
        description="Test description",
        image_prompt="A planet",
        video_prompt="Camera glides across the surface.",
    )
    scene = Scene(
        number=1,
        title="TEST SCENE",
        purpose="Test purpose",
        duration=5,
        shots=[shot],
    )
    config = ProjectConfig(
        metadata=ProjectMetadata(title="Test Project"),
        scenes=[scene],
    )

    generator = ScriptGenerator(templates_dir=templates_dir)
    output = generator.generate_script(config)

    assert "Wide shot." in output
    assert "smooth and intentional" in output
    assert config.scenes[0].shots[0].image_prompt == "A planet"
