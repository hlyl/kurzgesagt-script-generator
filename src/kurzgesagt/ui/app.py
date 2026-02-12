"""Streamlit UI for Kurzgesagt Script Generator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kurzgesagt.config import settings
from kurzgesagt.core import (
    AudioGenerator,
    ProjectManager,
    PromptOptimizer,
    ResolveExporter,
    SceneParser,
    ScriptGenerator,
    VideoGenerationError,
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
    configure_logging,
    ensure_directory,
    estimate_reading_time,
    get_logger,
    get_project_path,
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

    if "audio_generator" not in st.session_state:
        try:
            st.session_state.audio_generator = AudioGenerator()
        except Exception as e:
            st.warning(f"Audio generator not configured: {e}")
            st.session_state.audio_generator = None

    if "current_project" not in st.session_state:
        st.session_state.current_project = None

    if "config" not in st.session_state:
        st.session_state.config = None

    if "last_generated" not in st.session_state:
        st.session_state.last_generated = None

    if "last_parse" not in st.session_state:
        st.session_state.last_parse = None

    if "last_voice_over_hash" not in st.session_state:
        st.session_state.last_voice_over_hash = None


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

            if st.button("💾 Save Changes", width='stretch'):
                save_current_project()

            if st.button("🗑️ Delete Project", width='stretch'):
                delete_current_project()


def render_new_project_form() -> None:
    """Render form for creating new project."""
    with st.form("new_project_form"):
        project_title = st.text_input(
            "Project Title", placeholder="e.g., Data Classification Explained"
        )

        author = st.text_input("Author (optional)", placeholder="Your name")

        submitted = st.form_submit_button("Create Project", width='stretch')

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

    if st.button("Load", width='stretch'):
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


def update_shot_video_prompt(
    config: ProjectConfig,
    scene_number: int,
    shot_number: int,
    new_prompt: str
) -> bool:
    """Update video prompt for a specific shot.

    Args:
        config: Project configuration
        scene_number: Scene number
        shot_number: Shot number
        new_prompt: New video prompt text

    Returns:
        True if update was successful, False otherwise
    """
    try:
        # Find the scene
        scene = next((s for s in config.scenes if s.number == scene_number), None)
        if not scene:
            logger.error(f"Scene {scene_number} not found")
            return False

        # Find the shot
        shot = next((s for s in scene.shots if s.number == shot_number), None)
        if not shot:
            logger.error(f"Shot {shot_number} not found in scene {scene_number}")
            return False

        # Update the video prompt
        shot.video_prompt = new_prompt
        logger.info(f"Updated video prompt for Scene {scene_number} Shot {shot_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to update video prompt: {e}")
        return False


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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
        [
            "⚙️ Settings",
            "📋 Overview",
            "🎨 Style",
            "🎬 Script",
            "📄 Generate",
            "🖼 Images",
            "🎙️ Audio",
            "🎥 Img2Video",
            "📤 Export",
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

    with tab7:
        render_audio_tab(config)

    with tab8:
        render_img2video_tab(config)

    with tab9:
        render_export_tab(config)


def render_overview_tab(config: ProjectConfig) -> None:
    """Render project overview."""
    st.header("Project Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Scenes", config.scene_count)
    with col2:
        st.metric("Shots", config.shot_count)
    with col3:
        duration = int(config.total_duration)  # Convert float to int for formatting
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

    if "voice_over_text" not in st.session_state:
        st.session_state.voice_over_text = config.voice_over_script

    voice_over_input = st.text_area(
        "Paste your voice-over script here",
        height=400,
        help="Your complete voice-over narration",
        key="voice_over_text",
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
        col2.metric("Est. Duration", f"{int(est_duration)//60}:{int(est_duration)%60:02d}")

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


def _check_script_sync(config: ProjectConfig) -> bool:
    """Check if the voice-over script has changed since last parse.

    Returns:
        True if script is in sync with parsed scenes, False if it has changed
    """
    if not config.voice_over_script or not config.scenes:
        return True

    if not st.session_state.last_voice_over_hash:
        return True

    import hashlib
    current_hash = hashlib.md5(config.voice_over_script.encode()).hexdigest()
    return current_hash == st.session_state.last_voice_over_hash


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

            # Store hash of voice-over script to track changes
            import hashlib
            script_hash = hashlib.md5(config.voice_over_script.encode()).hexdigest()
            st.session_state.last_voice_over_hash = script_hash

            # Reset audio preview text since scenes have changed
            if "audio_script_preview_text" in st.session_state:
                del st.session_state.audio_script_preview_text

            st.session_state.last_parse = {
                "scene_count": len(scenes),
                "shot_count": sum(scene.shot_count for scene in scenes),
                "script_hash": script_hash,
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

    # Check if script has changed since last parse
    if not _check_script_sync(config):
        st.warning(
            "⚠️ **Script has been modified since last parse.** "
            "The generated documents may not reflect your latest changes. "
            "Go to the Script tab and re-parse to update the scenes."
        )

    st.caption(
        f"Scenes: {len(config.scenes)} • Shots: {sum(scene.shot_count for scene in config.scenes)}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Project Setup", width='stretch'):
            generate_and_download(config, "setup")

    with col2:
        if st.button("✅ Confirmations", width='stretch'):
            generate_and_download(config, "confirmations")

    with col3:
        if st.button("🎬 Full Script", width='stretch'):
            generate_and_download(config, "script")

    st.divider()

    # Full export
    if st.button(
        "📦 Export Complete Project", type="primary", width='stretch'
    ):
        export_complete_project(config)


def render_images_tab(config: ProjectConfig) -> None:
    """Render image generation interface with script upload."""
    st.header("Image Generation")
    st.caption(
        "Upload or paste the script content used to derive scene image prompts."
    )

    # Check if script has changed since last parse
    if config.scenes and not _check_script_sync(config):
        st.warning(
            "⚠️ **Script has been modified since last parse.** "
            "Images will be generated based on the previously parsed scenes. "
            "Go to the Script tab and re-parse to update the scenes with your latest changes."
        )

    st.subheader("Style Reference Image")
    st.caption(
        "Optional: Upload a reference image to guide the visual style of generated images."
    )
    reference_upload = st.file_uploader(
        "Upload style reference image",
        type=["png", "jpg", "jpeg", "webp"],
        help="The reference image is stored in the project assets folder.",
        key="style_reference_upload",
    )

    if reference_upload is not None:
        try:
            project_dir = get_project_path(
                settings.projects_dir, st.session_state.current_project
            )
            assets_dir = ensure_directory(project_dir / "assets")
            suffix = Path(reference_upload.name).suffix.lower() or ".png"
            reference_path = assets_dir / f"style_reference{suffix}"
            reference_path.write_bytes(reference_upload.read())
            config.style.reference_image_path = str(
                Path("assets") / reference_path.name
            )
            st.session_state.config = config
            st.success(f"✅ Saved reference image to {reference_path}")
        except Exception as exc:
            st.error(f"❌ Failed to save reference image: {exc}")

    if config.style.reference_image_path:
        st.write(
            f"Current reference: {config.style.reference_image_path}"
        )
        if st.button(
            "Clear Reference Image",
            width='stretch',
            key="style_reference_clear",
        ):
            config.style.reference_image_path = None
            st.session_state.config = config
            st.rerun()

    st.divider()

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
        height=220,
        key="image_source_text",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Parse Script Into Scenes",
            width='stretch',
            key="images_parse_script",
        ):
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
        if st.button(
            "Clear Script",
            width='stretch',
            key="images_clear_script",
        ):
            st.session_state.image_source_text = ""
            st.rerun()

    st.divider()

    st.subheader("Generate Images")
    st.caption("Generate one image per shot and save to the project folder.")

    if st.button(
        "Generate Scene Images",
        width='stretch',
        key="images_generate_all",
    ):
        generate_scene_images(config)

    if st.button(
        "Generate First Image",
        width='stretch',
        key="images_generate_first",
    ):
        generate_first_image(config)

    selectable_shots = []
    for scene in config.scenes:
        for shot in scene.shots:
            description = shot.description or shot.narration
            description = (description or "").strip()
            if len(description) > 60:
                description = f"{description[:57]}..."
            label = (
                f"Scene {scene.number} — {scene.title} | Shot {shot.number}: "
                f"{description}"
            )
            selectable_shots.append((label, scene.number, shot.number))

    selected_label = st.selectbox(
        "Generate image for",
        options=[item[0] for item in selectable_shots] or ["No shots available"],
        help="Select a shot to generate its image.",
        key="image_generate_select",
        disabled=not selectable_shots,
    )
    if st.button(
        "Generate Selected Image",
        width='stretch',
        key="images_generate_selected",
        disabled=not selectable_shots,
    ):
        selected_index = next(
            (
                idx + 1
                for idx, item in enumerate(selectable_shots)
                if item[0] == selected_label
            ),
            1,
        )
        generate_selected_image(config, int(selected_index))

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


def _load_reference_image_payload(
    config: ProjectConfig, project_dir: Path
) -> tuple[Optional[bytes], Optional[str]]:
    """Load reference image bytes and mime type if configured."""
    reference_path = config.style.reference_image_path
    if not reference_path:
        return None, None

    image_path = Path(reference_path)
    if not image_path.is_absolute():
        image_path = project_dir / image_path

    if not image_path.exists():
        return None, None

    suffix = image_path.suffix.lower()
    mime = "image/png"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"

    return image_path.read_bytes(), mime


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
    reference_payload = _load_reference_image_payload(config, project_dir)
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
                    reference_image_bytes=reference_payload[0],
                    reference_image_mime=reference_payload[1],
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
    reference_payload = _load_reference_image_payload(config, project_dir)

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
            reference_image_bytes=reference_payload[0],
            reference_image_mime=reference_payload[1],
        )
        status.update(label="First image generated", state="complete")
        st.success(f"✅ Saved {image_path}")
    except Exception as e:
        status.update(label="Image generation failed", state="error")
        st.error(f"❌ Image generation failed: {str(e)}")


def generate_selected_image(config: ProjectConfig, index: int) -> None:
    """Generate a specific image by index across all shots."""
    if not config.scenes:
        st.warning("⚠️ No scenes defined. Parse your script first.")
        return

    shots = [shot for scene in config.scenes for shot in scene.shots]
    if not shots:
        st.warning("⚠️ No shots defined. Parse your script first.")
        return

    total = len(shots)
    if index < 1 or index > total:
        st.warning(f"⚠️ Select a value between 1 and {total}.")
        return

    status = st.status("Generating selected image...", expanded=False)
    try:
        generator = ImageGenerator()
    except Exception as e:
        status.update(label="Image generator not configured", state="error")
        st.error(f"❌ {str(e)}")
        return

    project_dir = get_project_path(
        settings.projects_dir, st.session_state.current_project
    )
    reference_payload = _load_reference_image_payload(config, project_dir)

    try:
        running = 0
        selected_scene = None
        selected_shot = None
        for scene in config.scenes:
            for shot in scene.shots:
                running += 1
                if running == index:
                    selected_scene = scene
                    selected_shot = shot
                    break
            if selected_shot is not None:
                break

        if not selected_scene or not selected_shot:
            status.update(label="Image generation failed", state="error")
            st.error("❌ Unable to resolve selected shot.")
            return

        image_path = generator.save_shot_image(
            project_dir=project_dir,
            scene_number=selected_scene.number,
            shot_number=selected_shot.number,
            prompt=selected_shot.image_prompt,
            model=config.technical.image_model,
            aspect_ratio=config.technical.image_aspect_ratio.value,
            resolution=config.technical.image_resolution.value,
            style_context=config.style.aesthetic.description,
            reference_image_bytes=reference_payload[0],
            reference_image_mime=reference_payload[1],
        )
        status.update(label="Selected image generated", state="complete")
        st.success(
            f"✅ Saved {image_path} (Scene {selected_scene.number}, Shot {selected_shot.number})"
        )
    except Exception as e:
        status.update(label="Image generation failed", state="error")
        st.error(f"❌ Image generation failed: {str(e)}")


def render_audio_tab(config: ProjectConfig) -> None:
    """Render audio generation interface."""
    st.header("Audio Generation")
    st.caption("Generate text-to-speech audio for your script with automatic pauses.")

    if not st.session_state.audio_generator:
        st.warning(
            "⚠️ Audio generator not configured. Set OPENAI_API_KEY in .env file."
        )
        return

    if not config.scenes:
        st.warning("⚠️ No scenes defined. Parse your script in the Script tab first.")
        return

    # Check if script has changed since last parse
    if not _check_script_sync(config):
        st.warning(
            "⚠️ **Script has been modified since last parse.** "
            "The audio will be based on the previously parsed scenes. "
            "Go to the Script tab and re-parse to update the scenes with your latest changes."
        )

    # TTS Settings
    st.subheader("TTS Settings")
    col1, col2, col3 = st.columns(3)

    with col1:
        tts_model = st.selectbox(
            "TTS Model",
            options=["tts-1", "tts-1-hd"],
            index=0 if settings.openai_tts_model == "tts-1" else 1,
            help="tts-1 is faster, tts-1-hd has higher quality",
        )

    with col2:
        tts_voice = st.selectbox(
            "Voice",
            options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            index=["alloy", "echo", "fable", "onyx", "nova", "shimmer"].index(
                settings.openai_tts_voice
            ),
            help="Choose the voice for the narration",
        )

    with col3:
        tts_speed = st.slider(
            "Speed",
            min_value=0.25,
            max_value=4.0,
            value=settings.openai_tts_speed,
            step=0.25,
            help="Speech speed (1.0 is normal)",
        )

    st.divider()

    # Pause duration settings
    st.subheader("Pause Durations")
    col1, col2 = st.columns(2)

    with col1:
        section_pause = st.slider(
            "Break between sections (seconds)",
            min_value=0.0,
            max_value=5.0,
            value=2.0,
            step=0.5,
            help="Duration of silence between different scenes/sections",
            key="audio_section_pause"
        )

    with col2:
        shot_pause = st.slider(
            "Break between shots (seconds)",
            min_value=0.0,
            max_value=3.0,
            value=1.0,
            step=0.25,
            help="Duration of silence between shots within a scene",
            key="audio_shot_pause"
        )

    st.divider()

    # Display script structure
    st.subheader("Script Structure with Pauses")
    st.caption(
        "Preview the narration from your parsed scenes with pause markers. "
        "You can edit the narration directly below and it will be used for audio generation."
    )

    st.info(
        "💡 **Tip:** Any edits you make here are used immediately for audio generation. "
        "Use '💾 Save Changes to Project' if you want to update the project's scene data permanently."
    )

    # Build initial script preview
    if "audio_script_preview_text" not in st.session_state:
        st.session_state.audio_script_preview_text = _build_script_preview(
            config, shot_pause, section_pause
        )

    # Allow editing of the script preview
    edited_script = st.text_area(
        "Script with Pauses",
        value=st.session_state.audio_script_preview_text,
        height=400,
        help="This shows the narration with [PAUSE] markers indicating silence. You can edit this text.",
        key="audio_script_preview",
    )

    # Update the preview if changed
    if edited_script != st.session_state.audio_script_preview_text:
        st.session_state.audio_script_preview_text = edited_script

    # Add button to reset to original parsed script
    col_reset1, col_reset2, col_reset3 = st.columns([1, 1, 2])
    with col_reset1:
        if st.button("🔄 Reset to Parsed Script", help="Reset to the original parsed script from scenes"):
            st.session_state.audio_script_preview_text = _build_script_preview(
                config, shot_pause, section_pause
            )
            st.rerun()

    with col_reset2:
        if st.button("💾 Save Changes to Project", help="Update the scene narration with edited text"):
            if _update_scenes_from_preview(config, edited_script):
                st.success("✅ Scene narration updated successfully!")
                st.session_state.config = config
                # Update the hash since we've manually edited
                import hashlib
                script_hash = hashlib.md5(config.voice_over_script.encode()).hexdigest()
                st.session_state.last_voice_over_hash = script_hash
                st.rerun()
            else:
                st.error("❌ Failed to update scenes. Check the format.")

    st.divider()

    # Generate options
    st.subheader("Generate Audio")
    st.caption(
        f"Generate audio files with automatic pauses between scenes ({section_pause}s) "
        f"and shots ({shot_pause}s)."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "🎙️ Generate Full Audio",
            width='stretch',
            help="Generate a single audio file for the entire script with pauses",
        ):
            generate_full_audio(
                config, tts_model, tts_voice, tts_speed, shot_pause, section_pause
            )

    with col2:
        if st.button(
            "📂 Generate by Scene",
            width='stretch',
            help="Generate separate audio files for each scene",
        ):
            generate_audio_by_scene(config, tts_model, tts_voice, tts_speed)

    with col3:
        if st.button(
            "🎬 Generate by Shot",
            width='stretch',
            help="Generate separate audio files for each shot",
        ):
            generate_audio_by_shot(config, tts_model, tts_voice, tts_speed)

    # Scene/Shot selector for individual generation
    st.divider()
    st.subheader("Generate Individual Audio")

    # Use the edited preview text for the selector
    preview_text = st.session_state.get("audio_script_preview_text", "")
    if not preview_text:
        preview_text = _build_script_preview(config, shot_pause, section_pause)

    # Parse the preview text to get scene/shot structure
    scene_data = _parse_preview_text(preview_text)

    # Build scene/shot selector
    selectable_items = []
    for scene_info in scene_data:
        scene_narration = " ".join(scene_info['shot_texts'])
        preview = scene_narration[:60] + "..." if len(scene_narration) > 60 else scene_narration
        selectable_items.append((
            f"Scene {scene_info['number']}: {scene_info['title']}",
            "scene",
            scene_info['number'],
            None,
            scene_narration
        ))

        for shot_idx, shot_text in enumerate(scene_info['shot_texts'], start=1):
            preview = shot_text[:60] + "..." if len(shot_text) > 60 else shot_text
            selectable_items.append((
                f"  Shot {shot_idx}: {preview}",
                "shot",
                scene_info['number'],
                shot_idx,
                shot_text
            ))

    selected_item = st.selectbox(
        "Select scene or shot",
        options=[item[0] for item in selectable_items],
        help="Choose a specific scene or shot to generate audio for",
    )

    if st.button("Generate Selected Audio", width='stretch'):
        selected_index = next(
            (idx for idx, item in enumerate(selectable_items) if item[0] == selected_item),
            0,
        )
        item = selectable_items[selected_index]
        generate_selected_audio(config, item, tts_model, tts_voice, tts_speed)


def _build_script_preview(
    config: ProjectConfig,
    shot_pause_seconds: float = 1.0,
    section_pause_seconds: float = 2.0
) -> str:
    """Build a preview of the script with pause markers.

    Args:
        config: Project configuration
        shot_pause_seconds: Duration of pause between shots (default: 1.0)
        section_pause_seconds: Duration of pause between sections/scenes (default: 2.0)

    Returns:
        Script preview text with pause markers
    """
    parts = []

    for i, scene in enumerate(config.scenes):
        parts.append(f"=== SCENE {scene.number}: {scene.title} ===\n")

        for j, shot in enumerate(scene.shots):
            if shot.narration:
                parts.append(shot.narration)

                # Add pause marker between shots (except last shot in scene)
                if j < len(scene.shots) - 1:
                    parts.append(f"[PAUSE {shot_pause_seconds}s]")

        # Add pause marker between scenes (except last scene)
        if i < len(config.scenes) - 1:
            parts.append(f"\n[PAUSE {section_pause_seconds}s]\n")

    return "\n\n".join(parts)


def _parse_preview_text(preview_text: str) -> list[dict]:
    """Parse preview text into structured scene/shot data.

    Args:
        preview_text: Script preview text with scene markers and pause indicators

    Returns:
        List of dicts with scene_num, scene_title, and shot_texts
    """
    import re

    # Split by scene markers
    scene_pattern = r"=== SCENE (\d+): (.+?) ===\n"
    scene_splits = re.split(scene_pattern, preview_text)

    # First element is empty or content before first scene
    scene_data = []
    for i in range(1, len(scene_splits), 3):
        if i + 1 < len(scene_splits):
            scene_num = int(scene_splits[i])
            scene_title = scene_splits[i + 1].strip()
            scene_content = scene_splits[i + 2] if i + 2 < len(scene_splits) else ""

            # Remove pause markers and split into shots
            # Remove scene pause markers first (handles variable durations)
            scene_content = re.sub(r'\n\[PAUSE [\d.]+s\]\n', '', scene_content)

            # Split by shot pause markers (handles variable durations)
            shot_texts = re.split(r'\n\n\[PAUSE [\d.]+s\]\n\n', scene_content)

            scene_data.append({
                'number': scene_num,
                'title': scene_title,
                'shot_texts': [s.strip() for s in shot_texts if s.strip()]
            })

    return scene_data


def _update_scenes_from_preview(config: ProjectConfig, preview_text: str) -> bool:
    """Update scene narrations from edited preview text.

    Args:
        config: Project configuration
        preview_text: Edited script preview text with scene markers

    Returns:
        True if update was successful, False otherwise
    """
    try:
        scene_data = _parse_preview_text(preview_text)

        # Update scenes in config
        for scene_info in scene_data:
            # Find matching scene in config
            scene = next((s for s in config.scenes if s.number == scene_info['number']), None)
            if scene and scene_info['shot_texts']:
                # Update shot narrations
                for i, shot in enumerate(scene.shots):
                    if i < len(scene_info['shot_texts']):
                        shot.narration = scene_info['shot_texts'][i]

        return True

    except Exception as e:
        logger.error(f"Failed to update scenes from preview: {e}")
        return False


def _ms_to_timecode(milliseconds: int, fps: int = 30) -> str:
    """Convert milliseconds to timecode format.

    Args:
        milliseconds: Time in milliseconds
        fps: Frames per second (default: 30)

    Returns:
        Timecode string in format HH:MM:SS:FF
    """
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frames = int((total_seconds % 1) * fps)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def generate_full_audio(
    config: ProjectConfig,
    model: str,
    voice: str,
    speed: float,
    shot_pause_seconds: float = 1.0,
    section_pause_seconds: float = 2.0,
) -> None:
    """Generate a single audio file for the entire script with pauses.

    Args:
        config: Project configuration
        model: TTS model to use
        voice: Voice to use
        speed: Speech speed
        shot_pause_seconds: Duration of pause between shots in seconds
        section_pause_seconds: Duration of pause between sections/scenes in seconds
    """
    status = st.status("Generating full audio...", expanded=False)

    try:
        generator = st.session_state.audio_generator
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )
        audio_dir = ensure_directory(project_dir / "audio")

        # Use the edited preview text instead of config.scenes
        preview_text = st.session_state.get("audio_script_preview_text", "")
        if not preview_text:
            preview_text = _build_script_preview(config)

        # Parse the preview text to get scene/shot structure
        scene_data = _parse_preview_text(preview_text)

        if not scene_data:
            st.error("❌ No scenes found in preview text")
            return

        import json
        from io import BytesIO

        from pydub import AudioSegment

        combined_audio = AudioSegment.empty()
        total_scenes = len(scene_data)
        progress = st.progress(0.0)

        # Track timestamps for each scene and shot
        fps = 30  # Default FPS for DaVinci Resolve
        timeline_data = {
            "project_name": st.session_state.current_project,
            "total_duration_ms": 0,
            "fps": fps,
            "settings": {
                "tts_model": model,
                "tts_voice": voice,
                "tts_speed": speed,
                "shot_pause_seconds": shot_pause_seconds,
                "section_pause_seconds": section_pause_seconds,
            },
            "scenes": []
        }

        status.update(label="Generating audio segments...", state="running")

        current_time_ms = 0

        for scene_idx, scene_info in enumerate(scene_data):
            scene_start_ms = current_time_ms
            scene_shots = []

            for shot_idx, shot_text in enumerate(scene_info['shot_texts']):
                shot_start_ms = current_time_ms

                if shot_text and shot_text.strip():
                    # Generate audio for this shot
                    audio_bytes = generator.generate_audio_bytes(
                        text=shot_text,
                        model=model,
                        voice=voice,
                        speed=speed,
                    )

                    # Load as AudioSegment
                    audio_segment = AudioSegment.from_mp3(BytesIO(audio_bytes))
                    shot_duration_ms = len(audio_segment)
                    shot_duration_seconds = shot_duration_ms / 1000.0
                    combined_audio += audio_segment
                    current_time_ms += shot_duration_ms

                    # Update project config with actual audio duration
                    try:
                        pm = st.session_state.project_manager
                        pm.update_shot_duration(
                            project_name=st.session_state.current_project,
                            scene_number=scene_info['number'],
                            shot_number=shot_idx + 1,
                            actual_duration=shot_duration_seconds,
                        )
                    except Exception as e:
                        # Log warning but continue processing
                        st.warning(f"⚠️ Could not update duration for Scene {scene_info['number']}, Shot {shot_idx + 1}: {str(e)}")

                    # Record shot timing
                    scene_shots.append({
                        "shot_number": shot_idx + 1,
                        "start_ms": shot_start_ms,
                        "end_ms": current_time_ms,
                        "duration_ms": shot_duration_ms,
                        "start_timecode": _ms_to_timecode(shot_start_ms, fps),
                        "end_timecode": _ms_to_timecode(current_time_ms, fps),
                        "narration_preview": shot_text[:100] + "..." if len(shot_text) > 100 else shot_text
                    })

                    # Add pause between shots (except last shot in scene)
                    if shot_idx < len(scene_info['shot_texts']) - 1:
                        pause_ms = int(shot_pause_seconds * 1000)
                        combined_audio += AudioSegment.silent(duration=pause_ms)
                        current_time_ms += pause_ms

            scene_end_ms = current_time_ms

            # Record scene timing
            timeline_data["scenes"].append({
                "scene_number": scene_info['number'],
                "scene_title": scene_info['title'],
                "start_ms": scene_start_ms,
                "end_ms": scene_end_ms,
                "duration_ms": scene_end_ms - scene_start_ms,
                "start_timecode": _ms_to_timecode(scene_start_ms, fps),
                "end_timecode": _ms_to_timecode(scene_end_ms, fps),
                "shots": scene_shots
            })

            # Add pause between scenes (except last scene)
            if scene_idx < len(scene_data) - 1:
                pause_ms = int(section_pause_seconds * 1000)
                combined_audio += AudioSegment.silent(duration=pause_ms)
                current_time_ms += pause_ms

            progress.progress((scene_idx + 1) / total_scenes)

        # Update total duration
        timeline_data["total_duration_ms"] = current_time_ms
        timeline_data["total_duration_timecode"] = _ms_to_timecode(current_time_ms, fps)

        # Save combined audio
        output_path = audio_dir / "full_narration.mp3"
        status.update(label="Saving audio file...", state="running")
        combined_audio.export(output_path, format="mp3")

        # Save timeline data as JSON
        timeline_path = audio_dir / "timeline_timestamps.json"
        status.update(label="Saving timeline data...", state="running")
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(timeline_data, f, indent=2, ensure_ascii=False)

        status.update(label="Audio generation complete", state="complete")
        st.success(f"✅ Saved full audio to {output_path}")
        st.info(f"📊 Timeline timestamps saved to {timeline_path}")

        # Provide download buttons
        col1, col2 = st.columns(2)
        with col1:
            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Download Full Audio",
                    data=f.read(),
                    file_name="full_narration.mp3",
                    mime="audio/mpeg",
                )
        with col2:
            with open(timeline_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 Download Timeline JSON",
                    data=f.read(),
                    file_name="timeline_timestamps.json",
                    mime="application/json",
                )

    except ImportError:
        status.update(label="Missing dependency", state="error")
        st.error(
            "❌ pydub library is required for audio concatenation. "
            "Install it with: pip install pydub"
        )
    except Exception as e:
        status.update(label="Audio generation failed", state="error")
        st.error(f"❌ Audio generation failed: {str(e)}")


def generate_audio_by_scene(
    config: ProjectConfig, model: str, voice: str, speed: float
) -> None:
    """Generate separate audio files for each scene."""
    status = st.status("Generating scene audio...", expanded=False)

    try:
        generator = st.session_state.audio_generator
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        # Use the edited preview text instead of config.scenes
        preview_text = st.session_state.get("audio_script_preview_text", "")
        if not preview_text:
            preview_text = _build_script_preview(config)

        # Parse the preview text to get scene/shot structure
        scene_data = _parse_preview_text(preview_text)

        if not scene_data:
            st.error("❌ No scenes found in preview text")
            return

        total_scenes = len(scene_data)
        progress = st.progress(0.0)

        for scene_idx, scene_info in enumerate(scene_data):
            status.update(
                label=f"Generating Scene {scene_info['number']}: {scene_info['title']}",
                state="running",
            )

            # Combine all shot narrations for this scene
            scene_narration = " ".join(scene_info['shot_texts'])

            if scene_narration.strip():
                audio_path, actual_duration = generator.generate_scene_audio(
                    project_dir=project_dir,
                    scene_number=scene_info['number'],
                    narration=scene_narration,
                    model=model,
                    voice=voice,
                    speed=speed,
                )

                # Update project config with actual audio duration
                try:
                    pm = st.session_state.project_manager
                    pm.update_scene_duration(
                        project_name=st.session_state.current_project,
                        scene_number=scene_info['number'],
                        actual_duration=actual_duration,
                    )
                except Exception as e:
                    st.warning(f"⚠️ Could not update duration for Scene {scene_info['number']}: {str(e)}")

            progress.progress((scene_idx + 1) / total_scenes)

        status.update(label="Scene audio generation complete", state="complete")
        st.success(f"✅ Generated {total_scenes} scene audio files in {project_dir / 'audio'}")

    except Exception as e:
        status.update(label="Audio generation failed", state="error")
        st.error(f"❌ Audio generation failed: {str(e)}")


def generate_audio_by_shot(
    config: ProjectConfig, model: str, voice: str, speed: float
) -> None:
    """Generate separate audio files for each shot."""
    status = st.status("Generating shot audio...", expanded=False)

    try:
        generator = st.session_state.audio_generator
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        # Use the edited preview text instead of config.scenes
        preview_text = st.session_state.get("audio_script_preview_text", "")
        if not preview_text:
            preview_text = _build_script_preview(config)

        # Parse the preview text to get scene/shot structure
        scene_data = _parse_preview_text(preview_text)

        if not scene_data:
            st.error("❌ No scenes found in preview text")
            return

        # Count total shots
        total_shots = sum(len(scene_info['shot_texts']) for scene_info in scene_data)
        progress = st.progress(0.0)
        completed = 0

        for scene_info in scene_data:
            for shot_idx, shot_text in enumerate(scene_info['shot_texts'], start=1):
                if shot_text and shot_text.strip():
                    status.update(
                        label=f"Generating Scene {scene_info['number']}, Shot {shot_idx}",
                        state="running",
                    )

                    audio_path, actual_duration = generator.generate_shot_audio(
                        project_dir=project_dir,
                        scene_number=scene_info['number'],
                        shot_number=shot_idx,
                        narration=shot_text,
                        model=model,
                        voice=voice,
                        speed=speed,
                    )

                    # Update project config with actual audio duration
                    try:
                        pm = st.session_state.project_manager
                        pm.update_shot_duration(
                            project_name=st.session_state.current_project,
                            scene_number=scene_info['number'],
                            shot_number=shot_idx,
                            actual_duration=actual_duration,
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Could not update duration for Scene {scene_info['number']}, Shot {shot_idx}: {str(e)}")

                completed += 1
                progress.progress(completed / total_shots)

        status.update(label="Shot audio generation complete", state="complete")
        st.success(f"✅ Generated {total_shots} shot audio files in {project_dir / 'audio'}")

    except Exception as e:
        status.update(label="Audio generation failed", state="error")
        st.error(f"❌ Audio generation failed: {str(e)}")


def generate_selected_audio(
    config: ProjectConfig,
    item: tuple,
    model: str,
    voice: str,
    speed: float,
) -> None:
    """Generate audio for a selected scene or shot."""
    item_label, item_type, scene_num, shot_num, narration_text = item

    status = st.status("Generating audio...", expanded=False)

    try:
        generator = st.session_state.audio_generator
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        if item_type == "scene":
            status.update(label=f"Generating Scene {scene_num}...", state="running")
            audio_path, actual_duration = generator.generate_scene_audio(
                project_dir=project_dir,
                scene_number=scene_num,
                narration=narration_text,
                model=model,
                voice=voice,
                speed=speed,
            )

            # Update project config with actual duration
            try:
                pm = st.session_state.project_manager
                pm.update_scene_duration(
                    project_name=st.session_state.current_project,
                    scene_number=scene_num,
                    actual_duration=actual_duration,
                )
            except Exception as e:
                st.warning(f"⚠️ Could not update duration for Scene {scene_num}: {str(e)}")

        else:  # shot
            status.update(
                label=f"Generating Scene {scene_num}, Shot {shot_num}...",
                state="running",
            )
            audio_path, actual_duration = generator.generate_shot_audio(
                project_dir=project_dir,
                scene_number=scene_num,
                shot_number=shot_num,
                narration=narration_text,
                model=model,
                voice=voice,
                speed=speed,
            )

            # Update project config with actual duration
            try:
                pm = st.session_state.project_manager
                pm.update_shot_duration(
                    project_name=st.session_state.current_project,
                    scene_number=scene_num,
                    shot_number=shot_num,
                    actual_duration=actual_duration,
                )
            except Exception as e:
                st.warning(f"⚠️ Could not update duration for Scene {scene_num}, Shot {shot_num}: {str(e)}")

        status.update(label="Audio generated", state="complete")
        st.success(f"✅ Saved audio to {audio_path} (duration: {actual_duration:.2f}s)")

        # Provide download button
        with open(audio_path, "rb") as f:
            st.download_button(
                label="📥 Download Audio",
                data=f.read(),
                file_name=audio_path.name,
                mime="audio/mpeg",
            )

    except Exception as e:
        status.update(label="Audio generation failed", state="error")
        st.error(f"❌ Audio generation failed: {str(e)}")


def render_export_tab(config: ProjectConfig) -> None:
    """Render export interface for DaVinci Resolve and other post-production workflows."""
    st.header("📤 Post-Production Export")
    st.caption("Export your project for DaVinci Resolve and other video editing tools")

    # Check if timeline data exists
    project_dir = get_project_path(
        settings.projects_dir, st.session_state.current_project
    )
    timeline_path = project_dir / "audio" / "timeline_timestamps.json"

    if not timeline_path.exists():
        st.warning(
            "⚠️ **Generate full audio first** to create timeline data. "
            "Timeline timestamps are required for accurate exports."
        )
        st.info(
            "💡 **Why you need timeline data:**\n"
            "- Accurate shot timing and duration\n"
            "- Proper scene organization\n"
            "- Synchronized audio markers\n\n"
            "Go to the **🎙️ Audio** tab and click **'🎙️ Generate Full Audio'** first."
        )
        return

    # Load timeline data
    import json
    with open(timeline_path, "r") as f:
        timeline_data = json.load(f)

    # Display project stats
    st.subheader("Project Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Scenes", len(timeline_data.get('scenes', [])))
    with col2:
        total_shots = sum(len(s['shots']) for s in timeline_data.get('scenes', []))
        st.metric("Total Shots", total_shots)
    with col3:
        total_duration = timeline_data.get('total_duration_ms', 0) / 1000
        st.metric("Duration", f"{total_duration:.1f}s")
    with col4:
        # Check for generated assets
        videos_dir = project_dir / "videos"
        existing_videos = 0
        if videos_dir.exists():
            for scene_dir in videos_dir.iterdir():
                if scene_dir.is_dir():
                    existing_videos += len(list(scene_dir.glob("*.mp4")))
        st.metric("Videos Ready", f"{existing_videos}/{total_shots}")

    st.divider()

    # Export Settings
    st.subheader("⚙️ Export Settings")

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        fps = st.selectbox(
            "Frame Rate (FPS)",
            options=[23.976, 24, 25, 29.97, 30, 50, 59.94, 60],
            index=5,  # Default to 30 FPS
            help="Timeline frame rate for DaVinci Resolve project"
        )

        _resolution = st.selectbox(
            "Resolution",
            options=["1080p (1920x1080)", "4K (3840x2160)", "720p (1280x720)"],
            index=0,
            help="Target resolution for the timeline"
        )

    with col_set2:
        include_markers = st.checkbox(
            "Include Scene/Shot Markers",
            value=True,
            help="Add markers at each scene and shot transition"
        )

        organize_bins = st.checkbox(
            "Organize in Bins",
            value=True,
            help="Create bins/folders for each scene to organize media"
        )

    st.divider()

    # Complete Project Package Export
    st.subheader("📦 Complete Project Package")

    st.info(
        "💡 **All-in-one export** - Download everything you need for video editing:\n\n"
        "- All generated videos and images\n"
        "- Full audio narration\n"
        "- Timeline data and timestamps\n"
        "- EDL, FCPXML, and Python script\n"
        "- README with instructions"
    )

    if st.button(
        "📦 Download Complete Project Package",
        type="primary",
        use_container_width=True,
        help="Download a ZIP file with all project assets and export files"
    ):
        export_complete_package(config, fps, include_markers, organize_bins)

    st.divider()

    # DaVinci Resolve Export Section
    st.subheader("🎬 DaVinci Resolve Export")

    st.info(
        "💡 **About these exports:**\n\n"
        "**EDL (Edit Decision List)** - Industry standard format for cut lists and basic timeline structure. "
        "Best for simple cuts and transitions.\n\n"
        "**FCPXML** - XML format with full metadata support including markers, bins, and effects. "
        "Recommended for complex projects with organization.\n\n"
        "**Python Script** - Direct automation using DaVinci Resolve's Python API. "
        "Most powerful option for complete project setup."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📋 Export EDL",
            width='stretch',
            help="Generate CMX 3600 EDL file for cut lists and basic timeline structure",
            use_container_width=True
        ):
            export_resolve_edl(config, fps)

    with col2:
        if st.button(
            "📄 Export FCPXML",
            width='stretch',
            help="Generate Final Cut Pro XML with markers and organized bins",
            use_container_width=True
        ):
            export_resolve_fcpxml(config, fps, include_markers, organize_bins)

    with col3:
        if st.button(
            "🐍 Generate Resolve Script",
            width='stretch',
            help="Create Python script for direct DaVinci Resolve API automation",
            use_container_width=True
        ):
            export_resolve_script(config, fps, include_markers, organize_bins)

    st.divider()

    # Workflow Guide
    st.subheader("📚 Workflow Guide")

    with st.expander("How to use EDL in DaVinci Resolve", expanded=False):
        st.markdown("""
        ### Using EDL Files in DaVinci Resolve

        1. **Open DaVinci Resolve** and create a new project
        2. Go to **File** → **Import** → **Timeline** → **EDL**
        3. Select the exported `.edl` file
        4. Choose your timeline settings (frame rate, resolution)
        5. The timeline structure will be imported with all cuts

        **Note:** EDL is basic and doesn't include bins or markers. Use FCPXML for full organization.
        """)

    with st.expander("How to use FCPXML in DaVinci Resolve", expanded=False):
        st.markdown("""
        ### Using FCPXML Files in DaVinci Resolve

        1. **Open DaVinci Resolve** and create a new project
        2. Go to **File** → **Import** → **Timeline** → **Final Cut Pro XML**
        3. Select the exported `.fcpxml` file
        4. The timeline will be created with:
           - Scene and shot organization in bins
           - Markers at each transition
           - Proper timing and duration
        5. Link your media files (audio and video) to the timeline

        **Recommended for:** Complex projects with multiple scenes and organization needs.
        """)

    with st.expander("How to use Python Script with DaVinci Resolve", expanded=False):
        st.markdown(f"""
        ### Using Python API Script

        1. **Download the Python script** using the button above
        2. Copy the script to your project's audio directory:
           ```
           {project_dir}/audio/
           ```
        3. **Make sure DaVinci Resolve is running** (with Python API enabled)
        4. Open Terminal/Command Prompt and run:
           ```
           python3 {st.session_state.current_project}_resolve.py
           ```
        5. The script will automatically:
           - Create a new project
           - Import all media (audio, videos, images)
           - Set up the timeline with precise timing
           - Add markers and organize bins
           - Configure project settings

        **Most powerful option** - Completely automates project setup with zero manual work.

        **Requirements:**
        - DaVinci Resolve Studio (free version has limited API access)
        - Python 3.6+ installed
        - DaVinci Resolve must be running before executing the script
        """)

    st.divider()

    # Preview Timeline Structure
    st.subheader("📊 Timeline Preview")
    with st.expander("View Timeline Structure", expanded=False):
        st.caption("This shows how your project will be structured in DaVinci Resolve")

        for scene_data in timeline_data.get('scenes', []):
            scene_num = scene_data['scene_number']
            scene_title = next(
                (s.title for s in config.scenes if s.number == scene_num),
                f"Scene {scene_num}"
            )

            scene_start = scene_data['start_ms'] / 1000
            scene_duration = scene_data['duration_ms'] / 1000

            st.markdown(f"**🎬 Scene {scene_num}: {scene_title}**")
            st.caption(f"Start: {scene_start:.2f}s | Duration: {scene_duration:.2f}s")

            for shot_data in scene_data['shots']:
                shot_num = shot_data['shot_number']
                shot_start = shot_data['start_ms'] / 1000
                shot_duration = shot_data['duration_ms'] / 1000

                st.text(f"  └─ Shot {shot_num}: {shot_start:.2f}s - {shot_start + shot_duration:.2f}s ({shot_duration:.2f}s)")

            st.markdown("")

    st.divider()

    # Export Location Info
    exports_dir = settings.exports_dir / st.session_state.current_project
    st.info(f"📁 **Export Location:** `{exports_dir}`\n\nAll export files are saved here for easy access.")


def export_resolve_edl(config: ProjectConfig, fps: float = 30.0) -> None:
    """Export EDL file for DaVinci Resolve."""
    status = st.status("Exporting EDL...", expanded=False)

    try:
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        # Initialize exporter with custom FPS
        exporter = ResolveExporter(project_dir=project_dir, fps=fps)
        exporter.load_timeline_data()

        # Generate EDL
        exports_dir = settings.exports_dir / st.session_state.current_project
        edl_path = exports_dir / f"{st.session_state.current_project}.edl"

        status.update(label="Generating EDL file...", state="running")
        exporter.generate_edl(edl_path)

        status.update(label="EDL export complete", state="complete")
        st.success(f"✅ Exported EDL to {edl_path}")
        st.info(f"📊 **Settings:** {fps} FPS")

        # Provide download button
        with open(edl_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download EDL File",
                data=f.read(),
                file_name=edl_path.name,
                mime="text/plain",
            )

    except Exception as e:
        status.update(label="EDL export failed", state="error")
        st.error(f"❌ EDL export failed: {str(e)}")


def export_resolve_fcpxml(config: ProjectConfig, fps: float = 30.0, include_markers: bool = True, organize_bins: bool = True) -> None:
    """Export FCPXML file for DaVinci Resolve."""
    status = st.status("Exporting FCPXML...", expanded=False)

    try:
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        # Initialize exporter with custom FPS
        exporter = ResolveExporter(project_dir=project_dir, fps=fps)
        exporter.load_timeline_data()

        # Generate FCPXML
        exports_dir = settings.exports_dir / st.session_state.current_project
        fcpxml_path = exports_dir / f"{st.session_state.current_project}.fcpxml"

        status.update(label="Generating FCPXML file...", state="running")
        exporter.generate_fcpxml(fcpxml_path)

        status.update(label="FCPXML export complete", state="complete")
        st.success(f"✅ Exported FCPXML to {fcpxml_path}")
        st.info(
            f"📊 **Settings:** {fps} FPS | "
            f"Markers: {'✓' if include_markers else '✗'} | "
            f"Organized Bins: {'✓' if organize_bins else '✗'}"
        )

        # Provide download button
        with open(fcpxml_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download FCPXML File",
                data=f.read(),
                file_name=fcpxml_path.name,
                mime="application/xml",
            )

    except Exception as e:
        status.update(label="FCPXML export failed", state="error")
        st.error(f"❌ FCPXML export failed: {str(e)}")


def export_resolve_script(config: ProjectConfig, fps: float = 30.0, include_markers: bool = True, organize_bins: bool = True) -> None:
    """Generate Python script for Resolve API."""
    status = st.status("Generating Resolve script...", expanded=False)

    try:
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        # Initialize exporter with custom FPS
        exporter = ResolveExporter(project_dir=project_dir, fps=fps)
        exporter.load_timeline_data()

        # Generate Python script
        exports_dir = settings.exports_dir / st.session_state.current_project
        script_path = exports_dir / f"{st.session_state.current_project}_resolve.py"

        status.update(label="Generating Python script...", state="running")
        exporter.generate_resolve_script(script_path)

        status.update(label="Script generation complete", state="complete")
        st.success(f"✅ Generated Resolve script at {script_path}")
        st.info(
            f"📊 **Settings:** {fps} FPS | "
            f"Markers: {'✓' if include_markers else '✗'} | "
            f"Organized Bins: {'✓' if organize_bins else '✗'}"
        )
        st.info(
            "💡 **To use this script:**\n"
            "1. Make sure DaVinci Resolve is running\n"
            "2. Copy the script to your project's audio directory\n"
            f"3. Run: `python3 {st.session_state.current_project}_resolve.py`"
        )

        # Provide download button
        with open(script_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Download Python Script",
                data=f.read(),
                file_name=script_path.name,
                mime="text/x-python",
            )

    except Exception as e:
        status.update(label="Script generation failed", state="error")
        st.error(f"❌ Script generation failed: {str(e)}")


def export_complete_package(
    config: ProjectConfig,
    fps: float = 30.0,
    include_markers: bool = True,
    organize_bins: bool = True
) -> None:
    """Export complete project package as ZIP file."""
    import zipfile
    from datetime import datetime

    status = st.status("Creating project package...", expanded=True)

    try:
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )
        project_name = st.session_state.current_project

        # Create temporary export directory
        exports_dir = settings.exports_dir / project_name
        exports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize exporter
        exporter = ResolveExporter(project_dir=project_dir, fps=fps)
        exporter.load_timeline_data()

        status.update(label="Generating export files...", state="running")

        # Generate EDL
        edl_path = exports_dir / f"{project_name}.edl"
        exporter.generate_edl(edl_path)
        logger.info(f"Generated EDL: {edl_path}")

        # Generate FCPXML
        fcpxml_path = exports_dir / f"{project_name}.fcpxml"
        exporter.generate_fcpxml(fcpxml_path)
        logger.info(f"Generated FCPXML: {fcpxml_path}")

        # Generate Python script
        script_path = exports_dir / f"{project_name}_resolve.py"
        exporter.generate_resolve_script(script_path)
        logger.info(f"Generated Python script: {script_path}")

        # Create README
        status.update(label="Creating README...", state="running")
        readme_path = exports_dir / "README.md"
        readme_content = f"""# {project_name} - DaVinci Resolve Project Package

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Settings:** {fps} FPS | Markers: {'✓' if include_markers else '✗'} | Organized Bins: {'✓' if organize_bins else '✗'}

## 📁 Package Contents

### Media Files
- `videos/` - All generated video clips organized by scene
- `images/` - All generated images organized by scene
- `audio/` - Full narration audio and timeline data

### Export Files
- `{project_name}.edl` - Edit Decision List for basic timeline import
- `{project_name}.fcpxml` - Final Cut Pro XML with full metadata
- `{project_name}_resolve.py` - Python script for DaVinci Resolve API

### Timeline Data
- `audio/timeline_timestamps.json` - Precise timing data for all scenes and shots

## 🎬 How to Use in DaVinci Resolve

### Option 1: FCPXML Import (Recommended)
1. Open DaVinci Resolve
2. Go to **File** → **Import** → **Timeline** → **Final Cut Pro XML**
3. Select `{project_name}.fcpxml`
4. Link your media files from the `videos/`, `images/`, and `audio/` folders
5. Start editing!

### Option 2: Python API Script (Most Automated)
1. Make sure DaVinci Resolve Studio is running
2. Copy all files to a convenient location
3. Open Terminal/Command Prompt in the `audio/` directory
4. Run: `python3 {project_name}_resolve.py`
5. The script will automatically create the project and import all media

### Option 3: EDL Import (Basic)
1. Open DaVinci Resolve
2. Go to **File** → **Import** → **Timeline** → **EDL**
3. Select `{project_name}.edl`
4. Manually link media files

## 📊 Project Statistics

- **Total Duration:** {exporter.timeline_data.get('total_duration_ms', 0) / 1000:.1f}s
- **Scenes:** {len(exporter.timeline_data.get('scenes', []))}
- **Shots:** {sum(len(s['shots']) for s in exporter.timeline_data.get('scenes', []))}
- **Frame Rate:** {fps} FPS

## 📝 Notes

- Videos are in 9:16 aspect ratio (vertical format)
- Each video clip's duration matches the narration timing
- Audio file contains the full narration with proper pauses
- Timeline timestamps provide precise timing for manual editing

---

Generated with Kurzgesagt Script Generator
"""

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        logger.info(f"Created README: {readme_path}")

        # Create ZIP file
        status.update(label="Packaging files into ZIP...", state="running")
        zip_filename = f"{project_name}_package.zip"
        zip_path = exports_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add README
            zipf.write(readme_path, f"{project_name}/README.md")

            # Add export files
            zipf.write(edl_path, f"{project_name}/{edl_path.name}")
            zipf.write(fcpxml_path, f"{project_name}/{fcpxml_path.name}")
            zipf.write(script_path, f"{project_name}/{script_path.name}")

            # Add audio directory
            audio_dir = project_dir / "audio"
            if audio_dir.exists():
                for audio_file in audio_dir.rglob("*"):
                    if audio_file.is_file():
                        arcname = f"{project_name}/audio/{audio_file.relative_to(audio_dir)}"
                        zipf.write(audio_file, arcname)
                        logger.debug(f"Added to ZIP: {arcname}")

            # Add videos directory
            videos_dir = project_dir / "videos"
            if videos_dir.exists():
                for video_file in videos_dir.rglob("*.mp4"):
                    if video_file.is_file():
                        arcname = f"{project_name}/videos/{video_file.relative_to(videos_dir)}"
                        zipf.write(video_file, arcname)
                        logger.debug(f"Added to ZIP: {arcname}")

            # Add images directory
            images_dir = project_dir / "images"
            if images_dir.exists():
                for image_file in images_dir.rglob("*.png"):
                    if image_file.is_file():
                        arcname = f"{project_name}/images/{image_file.relative_to(images_dir)}"
                        zipf.write(image_file, arcname)
                        logger.debug(f"Added to ZIP: {arcname}")

        file_size_mb = zip_path.stat().st_size / (1024 * 1024)

        status.update(label="Package created successfully", state="complete")
        st.success(f"✅ Created project package: {zip_filename}")
        st.info(f"📦 **Package Size:** {file_size_mb:.2f} MB")

        # Provide download button
        with open(zip_path, "rb") as f:
            st.download_button(
                label="📥 Download Complete Package",
                data=f.read(),
                file_name=zip_filename,
                mime="application/zip",
            )

        # Show what's included
        with st.expander("📋 Package Contents", expanded=False):
            st.markdown(f"""
**Media Files:**
- Videos: `{project_name}/videos/scene_XX/shot_XX.mp4`
- Images: `{project_name}/images/scene_XX/shot_XX.png`
- Audio: `{project_name}/audio/full_narration.mp3`

**Export Files:**
- EDL: `{project_name}/{project_name}.edl`
- FCPXML: `{project_name}/{project_name}.fcpxml`
- Python Script: `{project_name}/{project_name}_resolve.py`

**Timeline Data:**
- Timestamps: `{project_name}/audio/timeline_timestamps.json`

**Documentation:**
- Instructions: `{project_name}/README.md`
            """)

    except Exception as e:
        status.update(label="Package creation failed", state="error")
        st.error(f"❌ Package creation failed: {str(e)}")
        logger.exception("Package creation error")


def render_img2video_tab(config: ProjectConfig) -> None:
    """Render image-to-video generation interface using Veo 3.1."""
    st.header("Image to Video Generation (Veo 3.1)")
    st.caption("Animate generated images with 9:16 aspect ratio, 8-second videos")

    # Check prerequisites
    project_dir = get_project_path(
        settings.projects_dir, st.session_state.current_project
    )
    images_dir = project_dir / "images"

    if not images_dir.exists() or not any(images_dir.iterdir()):
        st.warning("⚠️ No images found. Generate images in the Images tab first.")
        return

    # Load timeline for duration information
    timeline_path = project_dir / "audio" / "timeline_timestamps.json"
    has_timeline = timeline_path.exists()

    if has_timeline:
        import json
        with open(timeline_path, "r") as f:
            timeline_data = json.load(f)
        st.success("✅ Timeline data loaded. Videos will sync with audio in DaVinci Resolve.")
    else:
        st.info("💡 Generate full audio first for automatic duration sync in timeline.")
        timeline_data = None

    st.divider()

    # Video generation info
    st.subheader("Video Settings")
    col1, col2 = st.columns(2)

    with col1:
        st.info(
            "**Aspect Ratio**: 9:16 (Portrait)\n"
            "**Duration**: 8 seconds per video\n"
            "**Model**: Veo 3.1 (Google)"
        )
    with col2:
        st.caption(
            "Videos use the generated image as the first frame and "
            "animate key elements based on your selected style. "
            "The 8-second videos will be time-stretched in DaVinci Resolve "
            "to match actual narration timing."
        )

    st.divider()

    # Scan available images
    st.subheader("Available Images")

    available_shots = []
    missing_shots = []

    for scene in config.scenes:
        for shot in scene.shots:
            image_path = images_dir / f"scene_{scene.number:02d}" / f"shot_{shot.number:02d}.png"

            if image_path.exists():
                available_shots.append({
                    'scene': scene,
                    'shot': shot,
                    'image_path': image_path
                })
            else:
                missing_shots.append({
                    'scene_num': scene.number,
                    'scene_title': scene.title,
                    'shot_num': shot.number
                })

    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ready for Video", len(available_shots))
    with col2:
        st.metric("Missing Images", len(missing_shots))
    with col3:
        videos_dir = project_dir / "videos"
        existing_videos = 0
        if videos_dir.exists():
            for scene_dir in videos_dir.iterdir():
                if scene_dir.is_dir():
                    existing_videos += len(list(scene_dir.glob("*.mp4")))
        st.metric("Videos Generated", existing_videos)

    # Display missing images warning
    if missing_shots:
        with st.expander("⚠️ Missing Images - Generate These First", expanded=False):
            st.warning(
                "These shots need images before video generation. "
                "Go to the Images tab to generate them."
            )
            for item in missing_shots:
                st.text(
                    f"  • Scene {item['scene_num']}: {item['scene_title']} "
                    f"- Shot {item['shot_num']}"
                )

    # Available shots preview
    with st.expander("View available shots", expanded=False):
        for item in available_shots:
            scene = item['scene']
            shot = item['shot']

            # Get duration info
            duration_info = "8s → stretch in Resolve"
            if has_timeline and timeline_data:
                scene_data = next(
                    (s for s in timeline_data['scenes'] if s['scene_number'] == scene.number),
                    None
                )
                if scene_data:
                    shot_data = next(
                        (s for s in scene_data['shots'] if s['shot_number'] == shot.number),
                        None
                    )
                    if shot_data:
                        actual_duration = shot_data['duration_ms'] / 1000
                        duration_info = f"8s → {actual_duration:.1f}s"

            st.markdown(
                f"**Scene {scene.number} - Shot {shot.number}** ({duration_info})\n"
                f"- Elements: {', '.join(shot.key_elements[:3])}{'...' if len(shot.key_elements) > 3 else ''}\n"
                f"- Prompt: {shot.video_prompt[:80]}..."
            )

    st.divider()

    # Generation buttons
    st.subheader("Generate Videos")

    if not available_shots:
        st.warning("No images available for video generation.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "🎬 Generate All Videos",
            width='stretch',
            help="Generate videos for all available images (may take several minutes per video)"
        ):
            generate_all_videos(config, available_shots)

    with col2:
        if st.button(
            "🎞️ Generate by Scene",
            width='stretch',
            help="Select and generate videos for a specific scene"
        ):
            st.session_state.show_scene_selector = True

    with col3:
        if st.button(
            "🎥 Generate First Video",
            width='stretch',
            help="Test with first video only (faster)"
        ):
            generate_first_video(config, available_shots)

    # Scene selector (shown after clicking Generate by Scene)
    if st.session_state.get('show_scene_selector', False):
        st.divider()
        st.subheader("Select Scene")

        # Group shots by scene
        scenes_shots = {}
        for item in available_shots:
            scene_num = item['scene'].number
            if scene_num not in scenes_shots:
                scenes_shots[scene_num] = []
            scenes_shots[scene_num].append(item)

        scene_options = [
            f"Scene {num}: {items[0]['scene'].title} ({len(items)} shots)"
            for num, items in sorted(scenes_shots.items())
        ]

        selected_scene = st.selectbox(
            "Choose scene to generate",
            options=scene_options,
            key="scene_selector_video"
        )

        if st.button("Generate Scene Videos", width='stretch'):
            scene_num = int(selected_scene.split(":")[0].split()[1])
            scene_items = scenes_shots[scene_num]
            generate_all_videos(config, scene_items)

    # Individual shot selector with thumbnails
    st.divider()
    st.subheader("Generate Individual Video")

    # Dropdown to select shot
    shot_options = [
        f"Scene {item['scene'].number} - Shot {item['shot'].number}: "
        f"{item['shot'].narration[:60]}..."
        for item in available_shots
    ]

    selected = st.selectbox(
        "Select shot",
        options=shot_options,
        help="Choose specific shot to generate video",
        key="individual_shot_selector"
    )

    # Get selected shot details
    selected_index = shot_options.index(selected)
    selected_item = available_shots[selected_index]
    scene = selected_item['scene']
    shot = selected_item['shot']
    image_path = selected_item['image_path']

    # Display thumbnail and prompt in two columns
    col_left, col_right = st.columns([1, 2])

    with col_left:
        # Show image thumbnail
        st.image(
            str(image_path),
            caption=f"Scene {scene.number}, Shot {shot.number}",
            width='stretch'
        )

        # Show duration from project config (audio duration)
        st.markdown(f"**Duration:** {shot.duration:.2f}s")

        # Show transition duration
        st.caption(f"Transition: {shot.transition_duration:.1f}s")

    with col_right:
        # Editable video prompt with save button
        st.markdown("**Video Animation Prompt** ✏️")
        edited_prompt = st.text_area(
            "Edit the video animation prompt",
            value=shot.video_prompt,
            height=150,
            key=f"prompt_scene_{scene.number}_shot_{shot.number}",
            label_visibility="collapsed"
        )

        # Save button for video prompt
        col_save, col_reset = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save Prompt", key=f"save_prompt_{scene.number}_{shot.number}"):
                if update_shot_video_prompt(config, scene.number, shot.number, edited_prompt):
                    save_current_project()
                else:
                    st.error("❌ Failed to update video prompt")

        with col_reset:
            if st.button("↺ Reset", key=f"reset_prompt_{scene.number}_{shot.number}"):
                st.rerun()

        st.caption("💡 Edit the prompt above and click 'Save Prompt' to update")

        # Show key elements
        if shot.key_elements:
            st.markdown("**Key Elements:**")
            st.caption(", ".join(shot.key_elements))

        # Show narration
        with st.expander("View Narration"):
            st.write(shot.narration)

    # Generate button below the preview
    if st.button("🎬 Generate Video for Selected Shot", width='stretch', type="primary"):
        generate_selected_video(config, selected_item)


def generate_all_videos(
    config: ProjectConfig,
    available_shots: List[dict]
) -> None:
    """Generate videos for all available images."""
    status = st.status("Generating videos...", expanded=True)

    try:
        # Initialize VideoGenerator
        if not settings.gemini_api_key:
            status.update(label="API key missing", state="error")
            st.error("❌ GEMINI_API_KEY not configured in .env file")
            return

        from kurzgesagt.core import VideoGenerator

        generator = VideoGenerator(api_key=settings.gemini_api_key)
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        total = len(available_shots)
        progress = st.progress(0.0)

        generated_videos = []
        failed_videos = []

        for idx, item in enumerate(available_shots):
            scene = item['scene']
            shot = item['shot']
            image_path = item['image_path']

            # Get shot duration (capped at 8 seconds for API limit)
            shot_duration = min(int(shot.duration), 8)

            status.update(
                label=f"Generating Scene {scene.number} Shot {shot.number} - {shot_duration}s video ({idx+1}/{total})...",
                state="running"
            )

            try:
                # Get style context
                style_context = config.style.aesthetic.description

                # Generate video
                result = generator.save_shot_video(
                    project_dir=project_dir,
                    scene_number=scene.number,
                    shot_number=shot.number,
                    image_path=image_path,
                    video_prompt=shot.video_prompt,
                    key_elements=shot.key_elements,
                    style_context=style_context,
                    duration=shot_duration
                )

                if isinstance(result, Path):
                    # Success - video was downloaded and saved locally
                    generated_videos.append(result)
                    logger.info(f"Generated video: {result}")
                else:
                    # Manual download required - result is a URI
                    logger.warning(f"Video generated but requires manual download: {result}")
                    failed_videos.append({
                        'scene': scene.number,
                        'shot': shot.number,
                        'uri': result,
                        'message': 'Manual download required - automatic download failed'
                    })

            except VideoGenerationError as e:
                logger.error(f"Failed Scene {scene.number} Shot {shot.number}: {e}")
                failed_videos.append({
                    'scene': scene.number,
                    'shot': shot.number,
                    'uri': None,
                    'message': str(e)
                })
            except Exception as e:
                logger.error(f"Failed Scene {scene.number} Shot {shot.number}: {e}")
                failed_videos.append({
                    'scene': scene.number,
                    'shot': shot.number,
                    'uri': None,
                    'message': str(e)
                })

            progress.progress((idx + 1) / total)

        status.update(label="Video generation complete", state="complete")

        # Show results
        if generated_videos:
            st.success(f"✅ Generated {len(generated_videos)} videos!")

        if failed_videos:
            with st.expander("⚠️ Videos requiring manual download", expanded=True):
                st.info(
                    "Some videos were generated but couldn't be downloaded automatically. "
                    "Use the download commands below to get them."
                )

                for failure in failed_videos:
                    scene = failure['scene']
                    shot = failure['shot']
                    uri = failure.get('uri')
                    message = failure['message']

                    st.markdown(f"**Scene {scene}, Shot {shot}:** {message}")

                    if uri:
                        # Provide download command
                        download_cmd = f'python scripts/download_video.py "{uri}" "scene_{scene:02d}_shot_{shot:02d}.mp4"'
                        st.code(download_cmd, language="bash")
                        st.caption("Run this command in your terminal to download the video")

                    st.divider()

        # Show save location
        if generated_videos:
            videos_dir = project_dir / "videos"
            st.info(f"📁 Local videos saved to: {videos_dir}")

    except Exception as e:
        status.update(label="Video generation failed", state="error")
        st.error(f"❌ Video generation failed: {str(e)}")
        logger.exception("Video generation error")


def generate_first_video(
    config: ProjectConfig,
    available_shots: List[dict]
) -> None:
    """Generate only the first video for testing."""
    if not available_shots:
        st.warning("No shots available")
        return

    first_item = available_shots[0]
    generate_selected_video(config, first_item)


def generate_selected_video(
    config: ProjectConfig,
    selected_item: dict
) -> None:
    """Generate video for a specific shot."""
    status = st.status("Generating video...", expanded=False)

    try:
        # Check API key
        if not settings.gemini_api_key:
            status.update(label="API key missing", state="error")
            st.error("❌ GEMINI_API_KEY not configured in .env file")
            return

        from kurzgesagt.core import VideoGenerator

        generator = VideoGenerator(api_key=settings.gemini_api_key)
        project_dir = get_project_path(
            settings.projects_dir, st.session_state.current_project
        )

        scene = selected_item['scene']
        shot = selected_item['shot']
        image_path = selected_item['image_path']

        # Get shot duration (capped at 8 seconds for API limit)
        shot_duration = min(int(shot.duration), 8)

        status.update(
            label=f"Generating {shot_duration}s video (this may take 2-5 minutes)...",
            state="running"
        )

        # Get style context
        style_context = config.style.aesthetic.description

        # Generate video
        result = generator.save_shot_video(
            project_dir=project_dir,
            scene_number=scene.number,
            shot_number=shot.number,
            image_path=image_path,
            video_prompt=shot.video_prompt,
            key_elements=shot.key_elements,
            style_context=style_context,
            duration=shot_duration
        )

        status.update(label="Video generated", state="complete")

        if isinstance(result, Path):
            # Success - video was downloaded and saved locally
            st.success(f"✅ Video generated and saved to {result}")
            st.info(f"Scene {scene.number}, Shot {shot.number} - {shot_duration} seconds @ 9:16")
            st.video(str(result))

            # Show download button
            with open(result, "rb") as f:
                st.download_button(
                    label="📥 Download Video",
                    data=f.read(),
                    file_name=result.name,
                    mime="video/mp4"
                )
        else:
            # Manual download required - result is a URI
            st.warning(
                "⚠️ Video generated successfully but automatic download failed due to permissions."
            )
            st.info(
                "**How to fix this permanently:**\n\n"
                "1. Go to [Google Cloud Console](https://console.cloud.google.com/)\n"
                "2. Enable the Gemini API and set up billing\n"
                "3. Ensure your API key has Cloud Storage access permissions\n\n"
                "**For now, download your video manually:**"
            )
            st.markdown(f"🔗 [**Download Video Here**]({result})")
            st.caption("⏰ This link expires after a few hours")

    except VideoGenerationError as e:
        status.update(label="Video generation failed", state="error")
        st.error(f"❌ Video generation failed: {str(e)}")
        logger.exception("Video generation error")
    except Exception as e:
        status.update(label="Video generation failed", state="error")
        st.error(f"❌ Video generation failed: {str(e)}")
        logger.exception("Video generation error")


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
