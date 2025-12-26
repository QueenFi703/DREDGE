# DREDGE

**DREDGE** is a lightweight system for lifting, preserving, and releasing insights.

## Overview

DREDGE × Dolly is designed to move insights gracefully through their full lifecycle:

1. **Lift** — Heavy processing handled efficiently (GPU when available, CPU when not)
2. **Preserve** — Encrypted, internal persistence using secure storage
3. **Release** — Exportable to files, printable to paper, and shareable by design

## Installation

### From PyPI (once published)

```bash
pip install dredge
```

### From Source

```bash
git clone https://github.com/QueenFi703/DREDGE.git
cd DREDGE
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Show version
dredge --version

# Run as module
python -m dredge --version
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/QueenFi703/DREDGE.git
cd DREDGE

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run tests
pytest
```

### Building the Package

```bash
# Install build tools
pip install build

# Build distribution files
python -m build
```

## Requirements

- Python >= 3.10, < 3.13
- No external runtime dependencies

## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

QueenFi703

## Version

0.1.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
