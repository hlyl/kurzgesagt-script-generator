# Kurzgesagt Script Generator

Production-ready script generator for Kurzgesagt-style explainer videos.

## Features

- 🎨 **Professional Templates** - Kurzgesagt-style visual language
- 🤖 **AI Scene Parsing** - Automatic script breakdown using Claude
- 📝 **Model-Specific Optimization** - Optimized for Veo, Kling, Sora, and more
- 💾 **Project Management** - Save and organize multiple projects
- 📄 **Multi-Format Export** - Markdown, PDF, DOCX
- ✅ **Production Ready** - Full test coverage, type safety

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/kurzgesagt-script-generator
cd kurzgesagt-script-generator

# Install with UV
uv sync
uv sync --extra dev  # Install dev dependencies

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running the App
```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run Streamlit app
streamlit run src/kurzgesagt/ui/app.py
```

## Usage

1. **Create Project** - Start a new project or load existing
2. **Configure Style** - Set visual preferences and technical specs
3. **Add Script** - Paste your voice-over narration
4. **Parse Scenes** - Auto-generate scenes with Claude AI
5. **Generate Scripts** - Export production-ready documents

## Development

### Running Tests
```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/unit/test_models.py
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Project Structure
```
src/kurzgesagt/
├── models/          # Data models
├── core/            # Business logic
├── utils/           # Utilities
└── ui/              # Streamlit interface

templates/           # Jinja2 templates
projects/            # User projects (gitignored)
tests/               # Test suite
```

## License

MIT License - see LICENSE file for details