"""Streamlit UI for Kurzgesagt Script Generator."""

import streamlit as st
from pathlib import Path
from typing import Optional

from ..core import ProjectManager, ScriptGenerator, SceneParser, PromptOptimizer
from ..models import ProjectConfig, AspectRatio, ModelType, ShotComplexity
from ..utils import validate_project_name, ValidationError, estimate_reading_time
from ..config import settings


# Page configuration
st.set_page_config(
    page_title="Kurzgesagt Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
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
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state."""
    if 'project_manager' not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    
    if 'script_generator' not in st.session_state:
        st.session_state.script_generator = ScriptGenerator()
    
    if 'scene_parser' not in st.session_state:
        try:
            st.session_state.scene_parser = SceneParser()
        except Exception as e:
            st.warning(f"Claude API not configured: {e}")
            st.session_state.scene_parser = None
    
    if 'prompt_optimizer' not in st.session_state:
        st.session_state.prompt_optimizer = PromptOptimizer()
    
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    
    if 'config' not in st.session_state:
        st.session_state.config = None


def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<div class="main-header">🎬 Kurzgesagt Script Generator</div>', unsafe_allow_html=True)
    st.markdown("Generate production-ready video scripts in Kurzgesagt style")
    st.divider()
    
    # Sidebar: Project Management
    render_sidebar()
    
    # Main content area
    if st.session_state.config is not None:
        render_main_interface()
    else:
        render_welcome_screen()


def render_sidebar():
    """Render sidebar with project management."""
    with st.sidebar:
        st.title("📁 Projects")
        
        # Project selection
        option = st.radio(
            "Action",
            ["New Project", "Load Project"],
            label_visibility="collapsed"
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


def render_new_project_form():
    """Render form for creating new project."""
    with st.form("new_project_form"):
        project_title = st.text_input(
            "Project Title",
            placeholder="e.g., Data Classification Explained"
        )
        
        author = st.text_input(
            "Author (optional)",
            placeholder="Your name"
        )
        
        submitted = st.form_submit_button("Create Project", use_container_width=True)
        
        if submitted:
            if not project_title:
                st.error("Project title is required")
                return
            
            try:
                # Validate name
                project_name = validate_project_name(project_title)
                
                # Create project
                config = st.session_state.project_manager.create(
                    title=project_title,
                    author=author or None
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


def render_load_project_form():
    """Render form for loading existing project."""
    projects = st.session_state.project_manager.list_projects()
    
    if not projects:
        st.info("No projects found. Create a new one!")
        return
    
    selected = st.selectbox(
        "Select Project",
        options=projects,
        label_visibility="collapsed"
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


def save_current_project():
    """Save current project."""
    try:
        st.session_state.project_manager.save(
            st.session_state.config,
            st.session_state.current_project
        )
        st.success("✅ Project saved!")
    except Exception as e:
        st.error(f"❌ Failed to save: {str(e)}")


def delete_current_project():
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


def render_welcome_screen():
    """Render welcome screen when no project is loaded."""
    st.markdown("""
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
    """)


def render_main_interface():
    """Render main project interface."""
    config = st.session_state.config
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview",
        "🎨 Style",
        "🎬 Script",
        "📄 Generate",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_overview_tab(config)
    
    with tab2:
        render_style_tab(config)
    
    with tab3:
        render_script_tab(config)
    
    with tab4:
        render_generate_tab(config)
    
    with tab5:
        render_settings_tab(config)


def render_overview_tab(config: ProjectConfig):
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


def render_style_tab(config: ProjectConfig):
    """Render style configuration."""
    st.header("Visual Style Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Visual Language")
        
        config.style.aesthetic = st.text_input(
            "Aesthetic",
            value=config.style.aesthetic
        )
        
        config.style.color_palette = st.selectbox(
            "Color Palette",
            options=list(ColorPalette),
            format_func=lambda x: x.value.capitalize(),
            index=list(ColorPalette).index(config.style.color_palette)
        )
        
        config.style.line_work = st.selectbox(
            "Line Work",
            options=list(LineWork),
            format_func=lambda x: x.value.replace('_', ' ').title(),
            index=list(LineWork).index(config.style.line_work)
        )
    
    with col2:
        st.subheader("Motion")
        
        config.style.motion_pacing = st.selectbox(
            "Motion Pacing",
            options=list(MotionPacing),
            format_func=lambda x: x.value.capitalize(),
            index=list(MotionPacing).index(config.style.motion_pacing)
        )
        
        config.style.gradients = st.text_input(
            "Gradients",
            value=config.style.gradients
        )
        
        config.style.texture = st.text_input(
            "Texture",
            value=config.style.texture
        )


def render_script_tab(config: ProjectConfig):
    """Render script editing interface."""
    st.header("Voice-Over Script")
    
    config.voice_over_script = st.text_area(
        "Paste your voice-over script here",
        value=config.voice_over_script,
        height=400,
        help="Your complete voice-over narration"
    )
    
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
        st.warning("⚠️ Claude API not configured. Set ANTHROPIC_API_KEY in .env file.")
    else:
        if st.button("Parse Script into Scenes", type="primary"):
            if not config.voice_over_script:
                st.error("Please add a voice-over script first")
            else:
                parse_script_with_claude(config)


def parse_script_with_claude(config: ProjectConfig):
    """Parse script using Claude API."""
    with st.spinner("Parsing script with Claude..."):
        try:
            scenes = st.session_state.scene_parser.parse_script(
                voice_over=config.voice_over_script,
                style_guide=config.style,
                shot_complexity=config.technical.shot_complexity.value
            )
            
            config.scenes = scenes
            st.success(f"✅ Generated {len(scenes)} scenes with {sum(s.shot_count for s in scenes)} shots!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Parsing failed: {str(e)}")


def render_generate_tab(config: ProjectConfig):
    """Render script generation interface."""
    st.header("Generate Production Documents")
    
    if not config.scenes:
        st.warning("⚠️ No scenes defined. Parse your script or add scenes manually.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Project Setup", use_container_width=True):
            generate_and_download(config, 'setup')
    
    with col2:
        if st.button("✅ Confirmations", use_container_width=True):
            generate_and_download(config, 'confirmations')
    
    with col3:
        if st.button("🎬 Full Script", use_container_width=True):
            generate_and_download(config, 'script')
    
    st.divider()
    
    # Full export
    if st.button("📦 Export Complete Project", type="primary", use_container_width=True):
        export_complete_project(config)


def generate_and_download(config: ProjectConfig, doc_type: str):
    """Generate and provide download for specific document."""
    try:
        generator = st.session_state.script_generator
        
        if doc_type == 'setup':
            content = generator.generate_project_setup(config)
            filename = f"{st.session_state.current_project}_setup.md"
        elif doc_type == 'confirmations':
            content = generator.generate_confirmations(config)
            filename = f"{st.session_state.current_project}_confirmations.md"
        else:  # script
            content = generator.generate_script(config)
            filename = f"{st.session_state.current_project}_script.md"
        
        st.download_button(
            label=f"Download {doc_type.title()}",
            data=content,
            file_name=filename,
            mime="text/markdown"
        )
        
        st.success(f"✅ {doc_type.title()} generated!")
        
    except Exception as e:
        st.error(f"❌ Generation failed: {str(e)}")


def export_complete_project(config: ProjectConfig):
    """Export all project documents."""
    try:
        output_dir = settings.exports_dir / st.session_state.current_project
        
        saved_files = st.session_state.script_generator.save_outputs(
            config=config,
            output_dir=output_dir
        )
        
        st.success(f"✅ Exported {len(saved_files)} files to {output_dir}")
        
        for name, path in saved_files.items():
            st.write(f"- {name}: `{path}`")
        
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")


def render_settings_tab(config: ProjectConfig):
    """Render technical settings."""
    st.header("Technical Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config.technical.aspect_ratio = st.selectbox(
            "Aspect Ratio",
            options=list(AspectRatio),
            format_func=lambda x: x.value,
            index=list(AspectRatio).index(config.technical.aspect_ratio)
        )
        
        config.technical.model = st.selectbox(
            "Target Model",
            options=list(ModelType),
            format_func=lambda x: x.value.replace('_', ' ').title(),
            index=list(ModelType).index(config.technical.model)
        )
    
    with col2:
        config.technical.shot_complexity = st.selectbox(
            "Shot Complexity",
            options=list(ShotComplexity),
            format_func=lambda x: x.value.title(),
            index=list(ShotComplexity).index(config.technical.shot_complexity)
        )
        
        config.technical.text_on_screen = st.checkbox(
            "Include text overlays",
            value=config.technical.text_on_screen
        )


if __name__ == "__main__":
    main()