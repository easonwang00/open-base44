# Contributing to NativeBot

Thank you for your interest in contributing to NativeBot! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for testing Expo template output)
- An [Anthropic API key](https://console.anthropic.com)

### Getting Started

1. **Fork and clone the repository**

```bash
git clone https://github.com/<your-username>/nativebot.git
cd nativebot
```

2. **Set up the development environment**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

3. **Set your API key**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

4. **Run the CLI locally**

```bash
nativebot
```

Or run directly from source:

```bash
python -m nativebot.cli
```

## Project Layout

```
src/nativebot/
├── cli.py          # Click commands (entry point)
├── chat.py         # Interactive chat session with Claude
├── projects.py     # Project CRUD (filesystem-based)
├── agent.py        # Claude Agent SDK integration
├── constants.py    # Models, tools, system rules
└── display.py      # Rich terminal formatting
template/           # Expo seed template
pyproject.toml      # Package config + dependencies
```

## Pull Request Guidelines

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Keep PRs focused.** One feature or fix per PR. If you find an unrelated issue, open a separate PR.

3. **Write clear commit messages.** Use the imperative mood ("Add feature" not "Added feature").

4. **Test your changes** before submitting. Run `nativebot` and verify your change works end-to-end (create a project, chat, preview).

5. **Update documentation** if your change affects CLI commands, configuration, or the template.

6. **Open your PR against `main`** with a clear description of what changed and why.

## Code Style

- **Python:** Follow PEP 8. Use type hints where practical.
- **Naming:** Use descriptive variable and function names. Avoid abbreviations.
- **Comments:** Write comments for non-obvious logic. Code should be self-documenting where possible.

## What to Contribute

Here are some areas where contributions are especially welcome:

- **Bug fixes** -- check the Issues tab for reported bugs
- **Template improvements** -- better default Expo template, more starter components
- **CLI UX** -- better prompts, colors, progress indicators, error messages
- **Documentation** -- tutorials, guides, examples
- **Testing** -- unit tests, integration tests
- **Model support** -- adapting to new Claude model releases

See [VISION.md](VISION.md) for what we will and won't merge.

## Reporting Issues

When reporting a bug, please include:

- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Your environment (OS, Python version, Node version)
- Relevant error messages or terminal output

## Code of Conduct

Be respectful, inclusive, and constructive. We are building something together.

## Questions?

Open a [Discussion](https://github.com/nicepkg/nativebot/discussions) on GitHub if you have questions or want to propose a larger change before starting work.
