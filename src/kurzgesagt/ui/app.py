"""Streamlit UI for Kurzgesagt Script Generator."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kurzgesagt.config import settings
from kurzgesagt.core import (
    ProjectManager,
    PromptOptimizer,
    SceneParser,
    ScriptGenerator,
)
from kurzgesagt.core.image_generator import ImageGenerator
from kurzgesagt.models import ProjectConfig
from kurzgesagt.models.enums import (
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
from kurzgesagt.utils import (
    ValidationError,
    estimate_reading_time,
    get_project_path,
    get_logger,
    configure_logging,
    validate_optional_text,
    validate_project_name,
    validate_voice_over_script,
)

configure_logging()
logger = get_logger("ui")

# Page configuration
st.set_page_config(
    page_title="Kurzgesagt Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
def init_session_state() -> None:
    """Initialize Streamlit session state."""
    if "project_manager" not in st.session_state:
        st.session_state.project_manager = ProjectManager()

    if "script_generator" not in st.session_state:
        st.session_state.script_generator = ScriptGenerator()

    if "scene_parser" not in st.session_state:
        try:
            st.session_state.scene_parser = SceneParser()
        except Exception as e:
            st.warning(f"Scene parser not configured: {e}")
            st.session_state.scene_parser = None

    if "prompt_optimizer" not in st.session_state:
        st.session_state.prompt_optimizer = PromptOptimizer()

    if "current_project" not in st.session_state:
        st.session_state.current_project = None

    if "config" not in st.session_state:
        st.session_state.config = None

    if "last_generated" not in st.session_state:
        st.session_state.last_generated = None

    if "last_parse" not in st.session_state:
        st.session_state.last_parse = None


def main() -> None:
    """Main application entry point."""
    init_session_state()

    # Header
    st.markdown(
        '<div class="main-header">🎬 Kurzgesagt Script Generator</div>',
        unsafe_allow_html=True,
    )
    st.markdown("Generate production-ready video scripts in Kurzgesagt style")
    st.divider()

    # Sidebar: Project Management
    render_sidebar()

    # Main content area
    if st.session_state.config is not None:
        render_main_interface()
    else:
        render_welcome_screen()


def render_sidebar() -> None:
    """Render sidebar with project management."""
    with st.sidebar:
        st.title("📁 Projects")

        # Project selection
        option = st.radio(
            "Action", ["New Project", "Load Project"], label_visibility="collapsed"
        )

        if option == "New Project":
            render_new_project_form()
        else:
            render_load_project_form()

        st.divider()

        # Current project info
        if st.session_state.current_project:
            st.subheader("Current Project")
            st.info(f"📝 {st.session_state.current_project}")

            if st.button("💾 Save Changes", use_container_width=True):
                save_current_project()

            if st.button("🗑️ Delete Project", use_container_width=True):
                delete_current_project()


def render_new_project_form() -> None:
    """Render form for creating new project."""
    with st.form("new_project_form"):
        project_title = st.text_input(
            "Project Title", placeholder="e.g., Data Classification Explained"
        )

        author = st.text_input("Author (optional)", placeholder="Your name")

        submitted = st.form_submit_button("Create Project", use_container_width=True)

        if submitted:
            if not project_title:
                st.error("Project title is required")
                return

            try:
                # Validate name
                project_name = validate_project_name(project_title)

                safe_author = validate_optional_text(author, "Author")

                # Create project
                config = st.session_state.project_manager.create(
                    title=project_title, author=safe_author
                )

                # Set as current
                st.session_state.current_project = project_name
                st.session_state.config = config

                st.success(f"✅ Created project: {project_name}")
                st.rerun()

            except ValidationError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ Failed to create project: {str(e)}")


def render_load_project_form() -> None:
    """Render form for loading existing project."""
    projects = st.session_state.project_manager.list_projects()

    if not projects:
        st.info("No projects found. Create a new one!")
        return

    selected = st.selectbox(
        "Select Project", options=projects, label_visibility="collapsed"
    )

    if st.button("Load", use_container_width=True):
        try:
            config = st.session_state.project_manager.load(selected)
            st.session_state.current_project = selected
            st.session_state.config = config
            st.success(f"✅ Loaded: {selected}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to load project: {str(e)}")


def save_current_project() -> None:
    """Save current project."""
    try:
        st.session_state.project_manager.save(
            st.session_state.config, st.session_state.current_project
        )
        st.success("✅ Project saved!")
    except Exception as e:
        st.error(f"❌ Failed to save: {str(e)}")


def delete_current_project() -> None:
    """Delete current project with confirmation."""
    # This would ideally use a modal dialog
    confirm = st.checkbox("I understand this action cannot be undone")
    if confirm and st.button("Confirm Delete"):
        try:
            st.session_state.project_manager.delete(st.session_state.current_project)
            st.session_state.current_project = None
            st.session_state.config = None
            st.success("✅ Project deleted")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to delete: {str(e)}")


def render_welcome_screen() -> None:
    """Render welcome screen when no project is loaded."""
    st.markdown(
        """
    ## 👋 Welcome!

    Get started by creating a new project or loading an existing one from the sidebar.

    ### Features:
    - 🎨 Kurzgesagt-style visual templates
    - 🤖 AI-powered scene parsing
    - 📝 Model-specific prompt optimization
    - 📄 Multi-format export (MD, PDF, DOCX)

    ### Quick Start:
    1. Create a new project
    2. Configure your style preferences
    3. Paste your voice-over script
    4. Generate production-ready scripts
    """
    )


def render_main_interface() -> None:
    """Render main project interface."""
    config = st.session_state.config

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "⚙️ Settings",
            "📋 Overview",
            "🎨 Style",
            "🎬 Script",
            "📄 Generate",
            "🖼 Images",
        ]
    )

    with tab1:
        render_settings_tab(config)

    with tab2:
        render_overview_tab(config)

    with tab3:
        render_style_tab(config)

    with tab4:
        render_script_tab(config)

    with tab5:
        render_generate_tab(config)

    with tab6:
        render_images_tab(config)


def render_overview_tab(config: ProjectConfig) -> None:
    """Render project overview."""
    st.header("Project Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Scenes", config.scene_count)
    with col2:
        st.metric("Shots", config.shot_count)
    with col3:
        duration = config.total_duration
        st.metric("Duration", f"{duration//60}:{duration%60:02d}")

    st.divider()

    # Project info
    st.subheader("Details")
    st.write(f"**Title:** {config.metadata.title}")
    if config.metadata.description:
        st.write(f"**Description:** {config.metadata.description}")
    st.write(f"**Created:** {config.metadata.created_at.strftime('%Y-%m-%d %H:%M')}")
    st.write(f"**Updated:** {config.metadata.updated_at.strftime('%Y-%m-%d %H:%M')}")


def render_style_tab(config: ProjectConfig) -> None:
    """Render style configuration."""
    st.header("Visual Style Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Visual Language")

        config.style.aesthetic = st.selectbox(
            "Aesthetic",
            options=list(Aesthetic),
            format_func=lambda x: x.value.replace("_", " ").title(),
            index=list(Aesthetic).index(config.style.aesthetic),
        )
        st.caption(config.style.aesthetic.description)

        config.style.color_palette = st.selectbox(
            "Color Palette",
            options=list(ColorPalette),
            format_func=lambda x: x.value.capitalize(),
            index=list(ColorPalette).index(config.style.color_palette),
        )

        config.style.line_work = st.selectbox(
            "Line Work",
            options=list(LineWork),
            format_func=lambda x: x.value.replace("_", " ").title(),
            index=list(LineWork).index(config.style.line_work),
        )

    with col2:
        st.subheader("Motion")

        config.style.motion_pacing = st.selectbox(
            "Motion Pacing",
            options=list(MotionPacing),
            format_func=lambda x: x.value.capitalize(),
            index=list(MotionPacing).index(config.style.motion_pacing),
        )

        gradients_input = st.text_input(
            "Gradients",
            value=config.style.gradients,
        )
        try:
            config.style.gradients = (
                validate_optional_text(
                    gradients_input, "Gradients", max_length=200
                )
                or config.style.gradients
            )
        except ValidationError as e:
            st.error(str(e))

        texture_input = st.text_input("Texture", value=config.style.texture)
        try:
            config.style.texture = (
                validate_optional_text(
                    texture_input, "Texture", max_length=200
                )
                or config.style.texture
            )
        except ValidationError as e:
            st.error(str(e))


def render_script_tab(config: ProjectConfig) -> None:
    """Render script editing interface."""
    st.header("Voice-Over Script")

    voice_over_input = st.text_area(
        "Paste your voice-over script here",
        value=config.voice_over_script,
        height=400,
        help="Your complete voice-over narration",
    )

    try:
        if voice_over_input:
            validate_voice_over_script(voice_over_input)
        config.voice_over_script = voice_over_input
    except ValidationError as e:
        st.error(str(e))

    if config.voice_over_script:
        word_count = len(config.voice_over_script.split())
        est_duration = estimate_reading_time(config.voice_over_script)

        col1, col2 = st.columns(2)
        col1.metric("Word Count", word_count)
        col2.metric("Est. Duration", f"{est_duration//60}:{est_duration%60:02d}")

    st.divider()

    # Scene parsing
    st.subheader("🤖 Auto-Generate Scenes")

    if not st.session_state.scene_parser:
        st.warning(
            "⚠️ Scene parser not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env."
        )
    else:
        if st.button("Parse Script into Scenes", type="primary"):
            if not config.voice_over_script:
                st.error("Please add a voice-over script first")
            else:
                parse_script_with_claude(config)

    if config.scenes:
        st.divider()
        st.subheader("📌 Parsed Scenes Preview")
        with st.expander("View scenes", expanded=False):
            for scene in config.scenes:
                st.markdown(
                    f"**Scene {scene.number}:** {scene.title} (Shots: {scene.shot_count})"
                )
                for shot in scene.shots:
                    st.markdown(
                        f"- Shot {shot.number}: {shot.narration[:120]}"
                    )


def parse_script_with_claude(config: ProjectConfig) -> None:
    """Parse script using Claude API."""
    try:
        validate_voice_over_script(config.voice_over_script)
    except ValidationError as e:
        st.error(str(e))
        return

    with st.spinner("Parsing script with selected provider..."):
        try:
            scenes = st.session_state.scene_parser.parse_script(
                voice_over=config.voice_over_script,
                style_guide=config.style,
                shot_complexity=config.technical.shot_complexity.value,
            )

            config.scenes = scenes
            st.session_state.config = config
            st.session_state.last_parse = {
                "scene_count": len(scenes),
                "shot_count": sum(scene.shot_count for scene in scenes),
            }
            shot_total = sum(scene.shot_count for scene in scenes)
            st.success(
                f"✅ Generated {len(scenes)} scenes with {shot_total} shots!"
            )
            st.rerun()

        except Exception as e:
            st.error(f"❌ Parsing failed: {str(e)}")


def render_generate_tab(config: ProjectConfig) -> None:
    """Render script generation interface."""
    st.header("Generate Production Documents")

    if not config.scenes:
        st.warning("⚠️ No scenes defined. Parse your script or add scenes manually.")
        return

    st.caption(
        f"Scenes: {len(config.scenes)} • Shots: {sum(scene.shot_count for scene in config.scenes)}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Project Setup", use_container_width=True):
            generate_and_download(config, "setup")

    with col2:
        if st.button("✅ Confirmations", use_container_width=True):
            generate_and_download(config, "confirmations")

    with col3:
        if st.button("🎬 Full Script", use_container_width=True):
            generate_and_download(config, "script")

    st.divider()

    # Full export
    if st.button(
        "📦 Export Complete Project", type="primary", use_container_width=True
    ):
        export_complete_project(config)

    st.divider()

    st.subheader("🎨 Generate Scene Images")
    st.caption("Generate one image per shot and save to the project folder.")
    if st.button("Generate Scene Images", use_container_width=True):
        generate_scene_images(config)

    if st.button("Generate First Image", use_container_width=True):
        generate_first_image(config)

    with st.expander("View image generation prompts", expanded=False):
        prompt_lines = []
        for scene in config.scenes:
            for shot in scene.shots:
                prompt_lines.append(
                    f"Scene {scene.number} Shot {shot.number}: {shot.image_prompt}"
                )
        st.text_area(
            "Image Prompts",
            value="\n\n".join(prompt_lines) if prompt_lines else "",
            height=300,
            label_visibility="collapsed",
            key="image_prompt_preview",
        )

    render_generated_preview()


def render_images_tab(config: ProjectConfig) -> None:
    """Render image generation interface with script upload."""
    st.header("Image Generation")
    st.caption(
        "Upload or paste the script content used to derive scene image prompts."
    )

    uploaded = st.file_uploader(
        "Upload script file",
        type=["txt", "md"],
        help="Upload the full script or voice-over text.",
    )

    if uploaded is not None:
        try:
            file_text = uploaded.read().decode("utf-8", errors="ignore")
            st.session_state.image_source_text = file_text
        except Exception as exc:
            st.error(f"❌ Failed to read upload: {exc}")

    source_text = st.text_area(
        "Script for image generation",
        value=st.session_state.get("image_source_text", ""),
        height=220,
        key="image_source_text_area",
    )
    st.session_state.image_source_text = source_text

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Parse Script Into Scenes", use_container_width=True):
            if not source_text.strip():
                st.warning("⚠️ Please provide script content first.")
            elif not st.session_state.scene_parser:
                st.error("❌ Scene parser not configured.")
            else:
                try:
                    scenes = st.session_state.scene_parser.parse_script(
                        voice_over=source_text,
                        style_guide=config.style,
                        shot_complexity=config.technical.shot_complexity.value,
                    )
                    config.scenes = scenes
                    config.voice_over_script = source_text
                    st.session_state.config = config
                    st.success(
                        f"✅ Parsed {len(scenes)} scenes with {sum(scene.shot_count for scene in scenes)} shots."
                    )
                except Exception as exc:
                    st.error(f"❌ Parsing failed: {exc}")

    with col2:
        if st.button("Clear Script", use_container_width=True):
            st.session_state.image_source_text = ""
            st.rerun()

    st.divider()

    st.subheader("Generate Images")
    st.caption("Generate one image per shot and save to the project folder.")

    if st.button("Generate Scene Images", use_container_width=True):
        generate_scene_images(config)

    if st.button("Generate First Image", use_container_width=True):
        generate_first_image(config)

    with st.expander("View image generation prompts", expanded=False):
        prompt_lines = []
        for scene in config.scenes:
            for shot in scene.shots:
                prompt_lines.append(
                    f"Scene {scene.number} Shot {shot.number}: {shot.image_prompt}"
                )
        st.text_area(
            "Image Prompts",
            value="\n\n".join(prompt_lines) if prompt_lines else "",
            height=300,
            label_visibility="collapsed",
            key="image_prompt_preview_images_tab",
        )


def generate_and_download(config: ProjectConfig, doc_type: str) -> None:
    """Generate and provide download for specific document."""
    status = st.status("Generating document...", expanded=False)
    try:
        generator = st.session_state.script_generator

        if doc_type == "setup":
            status.update(label="Generating project setup...", state="running")
            content = generator.generate_project_setup(config)
            filename = f"{st.session_state.current_project}_setup.md"
        elif doc_type == "confirmations":
            status.update(label="Generating confirmations...", state="running")
            content = generator.generate_confirmations(config)
            filename = f"{st.session_state.current_project}_confirmations.md"
        else:  # script
            status.update(label="Generating full script...", state="running")
            content = generator.generate_script(config)
            filename = f"{st.session_state.current_project}_script.md"

        st.session_state.last_generated = {
            "doc_type": doc_type,
            "content": content,
            "filename": filename,
        }

        preview_key = f"preview_{doc_type}"
        if preview_key not in st.session_state:
            st.session_state[preview_key] = content

        with st.expander(f"Preview {doc_type.title()}", expanded=True):
            edited_content = st.text_area(
                "Preview",
                value=st.session_state[preview_key],
                height=400,
                label_visibility="collapsed",
                key=preview_key,
            )

        if edited_content != content:
            content = edited_content
            st.session_state.last_generated["content"] = edited_content

        status.update(label="Preparing download...", state="running")
        st.download_button(
            label=f"Download {doc_type.title()}",
            data=content,
            file_name=filename,
            mime="text/markdown",
        )

        status.update(label=f"{doc_type.title()} generated", state="complete")

    except Exception as e:
        status.update(label="Generation failed", state="error")
        st.error(f"❌ Generation failed: {str(e)}")


def export_complete_project(config: ProjectConfig) -> None:
    """Export all project documents."""
    status = st.status("Exporting project...", expanded=False)
    try:
        output_dir = settings.exports_dir / st.session_state.current_project
        status.update(label="Writing files...", state="running")

        saved_files = st.session_state.script_generator.save_outputs(
            config=config, output_dir=output_dir
        )

        status.update(label="Export complete", state="complete")
        st.success(f"✅ Exported {len(saved_files)} files to {output_dir}")

        for name, path in saved_files.items():
            st.write(f"- {name}: `{path}`")

    except Exception as e:
        status.update(label="Export failed", state="error")
        st.error(f"❌ Export failed: {str(e)}")


def render_generated_preview() -> None:
    """Render a full-width preview of the last generated document."""
    last = st.session_state.get("last_generated")
    if not last:
        return

    doc_type = last.get("doc_type", "document")
    content = last.get("content", "")

    st.divider()
    preview_key = "preview_last_generated"
    if preview_key not in st.session_state:
        st.session_state[preview_key] = content

    with st.expander(f"Preview {str(doc_type).title()}", expanded=False):
        edited_content = st.text_area(
            "Preview",
            value=st.session_state[preview_key],
            height=400,
            label_visibility="collapsed",
            key=preview_key,
        )

    if edited_content != content:
        st.session_state.last_generated["content"] = edited_content


def generate_scene_images(config: ProjectConfig) -> None:
    """Generate images for each shot and store under the project folder."""
    if not config.scenes:
        st.warning("⚠️ No scenes defined. Parse your script first.")
        return

    status = st.status("Generating scene images...", expanded=False)
    try:
        generator = ImageGenerator()
    except Exception as e:
        status.update(label="Image generator not configured", state="error")
        st.error(f"❌ {str(e)}")
        return

    project_dir = get_project_path(
        settings.projects_dir, st.session_state.current_project
    )
    total_shots = sum(len(scene.shots) for scene in config.scenes)
    progress = st.progress(0.0)
    completed = 0

    try:
        for scene in config.scenes:
            for shot in scene.shots:
                status.update(
                    label=(
                        f"Generating Scene {scene.number}, Shot {shot.number}"
                    ),
                    state="running",
                )
                generator.save_shot_image(
                    project_dir=project_dir,
                    scene_number=scene.number,
                    shot_number=shot.number,
                    prompt=shot.image_prompt,
                    model=config.technical.image_model,
                    aspect_ratio=config.technical.image_aspect_ratio.value,
                    resolution=config.technical.image_resolution.value,
                    style_context=config.style.aesthetic.description,
                )
                completed += 1
                if total_shots:
                    progress.progress(completed / total_shots)

        status.update(label="Image generation complete", state="complete")
        st.success(f"✅ Saved images to {project_dir / 'images'}")
    except Exception as e:
        status.update(label="Image generation failed", state="error")
        st.error(f"❌ Image generation failed: {str(e)}")


def generate_first_image(config: ProjectConfig) -> None:
    """Generate only the first scene/shot image."""
    if not config.scenes or not config.scenes[0].shots:
        st.warning("⚠️ No scenes or shots defined. Parse your script first.")
        return

    status = st.status("Generating first image...", expanded=False)
    try:
        generator = ImageGenerator()
    except Exception as e:
        status.update(label="Image generator not configured", state="error")
        st.error(f"❌ {str(e)}")
        return

    first_scene = config.scenes[0]
    first_shot = first_scene.shots[0]
    project_dir = get_project_path(
        settings.projects_dir, st.session_state.current_project
    )

    try:
        image_path = generator.save_shot_image(
            project_dir=project_dir,
            scene_number=first_scene.number,
            shot_number=first_shot.number,
            prompt=first_shot.image_prompt,
            model=config.technical.image_model,
            aspect_ratio=config.technical.image_aspect_ratio.value,
            resolution=config.technical.image_resolution.value,
            style_context=config.style.aesthetic.description,
        )
        status.update(label="First image generated", state="complete")
        st.success(f"✅ Saved {image_path}")
    except Exception as e:
        status.update(label="Image generation failed", state="error")
        st.error(f"❌ Image generation failed: {str(e)}")


def render_settings_tab(config: ProjectConfig) -> None:
    """Render technical settings."""
    st.header("Technical Settings")

    col1, col2 = st.columns(2)

    with col1:
        config.technical.aspect_ratio = st.selectbox(
            "Aspect Ratio",
            options=list(AspectRatio),
            format_func=lambda x: x.value,
            index=list(AspectRatio).index(config.technical.aspect_ratio),
        )

        config.technical.model = st.selectbox(
            "Target Model",
            options=list(ModelType),
            format_func=lambda x: x.value.replace("_", " ").title(),
            index=list(ModelType).index(config.technical.model),
        )

    with col2:
        config.technical.shot_complexity = st.selectbox(
            "Shot Complexity",
            options=list(ShotComplexity),
            format_func=lambda x: x.value.title(),
            index=list(ShotComplexity).index(config.technical.shot_complexity),
        )

        config.technical.text_on_screen = st.checkbox(
            "Include text overlays", value=config.technical.text_on_screen
        )

    st.divider()
    st.subheader("Image Generation")

    image_models = [
        settings.gemini_image_model,
        settings.gemini_image_model_alt,
    ]
    config.technical.image_model = st.selectbox(
        "Image Model",
        options=image_models,
        index=image_models.index(config.technical.image_model)
        if config.technical.image_model in image_models
        else 0,
    )

    config.technical.image_aspect_ratio = st.selectbox(
        "Image Aspect Ratio",
        options=list(ImageAspectRatio),
        format_func=lambda x: x.value,
        index=list(ImageAspectRatio).index(config.technical.image_aspect_ratio),
    )

    config.technical.image_resolution = st.selectbox(
        "Image Resolution",
        options=list(ImageResolution),
        format_func=lambda x: x.value,
        index=list(ImageResolution).index(config.technical.image_resolution),
    )


if __name__ == "__main__":
    main()
