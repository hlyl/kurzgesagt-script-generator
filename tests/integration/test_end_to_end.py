"""Integration tests for complete workflows."""


from src.kurzgesagt.core import ProjectManager, SceneParser, ScriptGenerator


def test_complete_workflow(temp_dir, templates_dir, mock_anthropic_client):
    """Test complete project workflow."""
    # 1. Create project
    pm = ProjectManager(base_path=temp_dir)
    config = pm.create(title="Integration Test")

    # 2. Add voice-over
    config.voice_over_script = "This is a test script for integration testing."

    # 3. Parse scenes
    parser = SceneParser(api_key="test_key", provider_name="anthropic")
    scenes = parser.parse_script(
        voice_over=config.voice_over_script, style_guide=config.style
    )
    config.scenes = scenes

    # 4. Save project
    pm.save(config, "integration-test")

    # 5. Generate scripts
    sg = ScriptGenerator(templates_dir=templates_dir)
    outputs = sg.generate_all(config)

    assert "project_setup" in outputs
    assert "confirmations" in outputs
    assert "full_script" in outputs
    assert len(outputs["full_script"]) > 0


def test_export_workflow(temp_dir, templates_dir, sample_project_config, sample_scene):
    """Test export workflow."""
    sample_project_config.scenes = [sample_scene]

    pm = ProjectManager(base_path=temp_dir)
    pm.save(sample_project_config, "export-test")

    sg = ScriptGenerator(templates_dir=templates_dir)
    output_dir = temp_dir / "exports"

    saved_files = sg.save_outputs(config=sample_project_config, output_dir=output_dir)

    assert len(saved_files) == 3
    assert all(path.exists() for path in saved_files.values())
