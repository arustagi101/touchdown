# Touchdown

A FastAPI application managed with uv.

## Getting Started

### Installing Dependencies

Use `uv add` to add new dependencies to your project:

```bash
# Add a production dependency
uv add requests

# Add a development dependency
uv add --dev pytest
```

### Running the FastAPI Application

Use FastAPI's development server:

```bash
uv run fastapi dev app/main.py
```

The application will be available at:
- Main endpoint: http://localhost:8000/
- Health check: http://localhost:8000/health
- API endpoint: http://localhost:8000/api/v1/touchdown
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The `uv run` command automatically manages the virtual environment and ensures all dependencies are available.