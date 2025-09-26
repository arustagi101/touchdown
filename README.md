# Touchdown

A Python project managed with uv.

## Getting Started

### Installing Dependencies

Use `uv add` to add new dependencies to your project:

```bash
# Add a production dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Add a dependency with version constraints
uv add "django>=4.0,<5.0"

# Add an optional dependency group
uv add --optional web fastapi uvicorn
```

### Running Commands

Use `uv run` to execute commands in the project environment:

```bash
# Run a Python script
uv run python main.py

# Run a module
uv run -m pytest

# Run with arguments
uv run python script.py --verbose

# Run any installed console script
uv run mypy src/
```

The `uv run` command automatically manages the virtual environment and ensures all dependencies are available.