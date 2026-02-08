# Kurzgesagt Script Generator

Production-ready script generator for Kurzgesagt-style explainer videos.

## Features

- 🎨 **Professional Templates** - Kurzgesagt-style visual language
- 🤖 **AI Scene Parsing** - Automatic script breakdown using Claude (optional)
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
# Create or edit .env and add your ANTHROPIC_API_KEY (required only for Claude parsing)
```

### Running the App
```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run Streamlit app (primary entrypoint)
streamlit run src/kurzgesagt/ui/app.py

# Note: You can run without ANTHROPIC_API_KEY; parsing will be disabled.
```

## Usage

1. **Create Project** - Start a new project or load existing
2. **Configure Style** - Set visual preferences and technical specs
3. **Add Script** - Paste your voice-over narration
4. **Parse Scenes** - Auto-generate scenes with Claude AI (requires API key)
5. **Generate Scripts** - Export production-ready documents

## API Keys Setup

Claude parsing is optional. You can run the app without a key, but the **Parse Scenes** button will be disabled.

Create or edit .env in the project root:
```dotenv
ANTHROPIC_API_KEY=your_real_key_here
```

Optional settings are already defined in .env (model, token limits, ports), and can be customized as needed.

## Examples

**Example Voice-Over (short):**
```text
Imagine sorting a huge pile of photos. Now imagine doing that with data.
Classification is how computers learn to recognize patterns and put things into categories.
```

**Expected outcome:**
- The parser generates scenes and shots with image/video prompts.
- The generator exports setup, confirmations, and full script documents.

## Example Projects Included

There is a sample project you can load immediately:

- projects/example_data_classification/
	- project_config.yaml
	- voice_over.txt

Open the app and load **example_data_classification** from the sidebar to explore a complete workflow.

## Troubleshooting

**“Claude API not configured” warning**
- Ensure ANTHROPIC_API_KEY is set in .env.
- Restart the Streamlit app after updating .env.

**Authentication error (invalid x-api-key)**
- Confirm the key is correct and active in your Anthropic account.

**Module not found errors (streamlit/anthropic/pydantic)**
- Run `uv sync` (or `uv sync --extra dev` for dev tools).

**Port 8501 already in use**
- Stop the other process, or change STREAMLIT_SERVER_PORT in .env.

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