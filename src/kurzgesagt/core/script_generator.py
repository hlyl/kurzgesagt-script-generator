"""Script generation using Jinja2 templates."""

from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from ..models import ProjectConfig, ModelType
from ..config import settings


class TemplateNotFoundError(Exception):
    """Raised when template file is not found."""
    pass


class ScriptGenerator:
    """Generates production scripts from templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize script generator.
        
        Args:
            templates_dir: Path to templates directory
        """
        self.templates_dir = templates_dir or settings.templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )
        
        # Add custom filters
        self.env.filters['duration_format'] = self._format_duration
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration as MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    
    def _get_template(self, template_name: str) -> Template:
        """
        Load a template by name.
        
        Args:
            template_name: Template filename
            
        Returns:
            Loaded Jinja2 template
            
        Raises:
            TemplateNotFoundError: If template doesn't exist
        """
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template '{template_name}' not found") from e
    
    def generate_project_setup(self, config: ProjectConfig) -> str:
        """
        Generate Stage 1: Project Setup Document.
        
        Args:
            config: Project configuration
            
        Returns:
            Rendered markdown
        """
        template = self._get_template('project_setup.md.j2')
        return template.render(project=config)
    
    def generate_confirmations(self, config: ProjectConfig) -> str:
        """
        Generate Stage 2: Production Confirmations.
        
        Args:
            config: Project configuration
            
        Returns:
            Rendered markdown
        """
        template = self._get_template('confirmations.md.j2')
        return template.render(project=config)
    
    def generate_script(self, config: ProjectConfig) -> str:
        """
        Generate Stage 3: Full Production Script.
        
        Uses model-specific template if available, falls back to generic.
        
        Args:
            config: Project configuration
            
        Returns:
            Rendered markdown script
        """
        # Try model-specific template first
        model_template = f"models/{config.technical.model.value}.md.j2"
        
        try:
            template = self._get_template(model_template)
        except TemplateNotFoundError:
            # Fallback to generic template
            template = self._get_template('script_structure.md.j2')
        
        return template.render(project=config)
    
    def generate_all(self, config: ProjectConfig) -> Dict[str, str]:
        """
        Generate all production documents.
        
        Args:
            config: Project configuration
            
        Returns:
            Dictionary with all rendered documents
        """
        return {
            'project_setup': self.generate_project_setup(config),
            'confirmations': self.generate_confirmations(config),
            'full_script': self.generate_script(config),
        }
    
    def save_outputs(
        self,
        config: ProjectConfig,
        output_dir: Path,
        include_setup: bool = True,
        include_confirmations: bool = True,
        include_script: bool = True,
    ) -> Dict[str, Path]:
        """
        Generate and save all outputs to directory.
        
        Args:
            config: Project configuration
            output_dir: Directory to save outputs
            include_setup: Whether to include setup document
            include_confirmations: Whether to include confirmations
            include_script: Whether to include full script
            
        Returns:
            Dictionary mapping document type to saved file path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = {}
        
        if include_setup:
            content = self.generate_project_setup(config)
            path = output_dir / "01_project_setup.md"
            path.write_text(content, encoding='utf-8')
            saved_files['project_setup'] = path
        
        if include_confirmations:
            content = self.generate_confirmations(config)
            path = output_dir / "02_confirmations.md"
            path.write_text(content, encoding='utf-8')
            saved_files['confirmations'] = path
        
        if include_script:
            content = self.generate_script(config)
            path = output_dir / "03_production_script.md"
            path.write_text(content, encoding='utf-8')
            saved_files['full_script'] = path
        
        return saved_files