# Custom CUDA/C++ Ops (Preview)

## What this adds
- A sample fused op (`fused_wave`) implemented in C++/CUDA, exposed to Python.
- Automatic runtime import with a CPU fallback if CUDA/nvcc isn't available.

## Build (GPU)
```bash
pip install -e .  # builds extensions if nvcc is present
```

## Build (CPU-only)
- Extensions are skipped; Python fallback is used automatically.

## Use
```python
from dredge.custom_ops import fused_wave
y = fused_wave(x, alpha=0.5)  # uses CUDA if built, else Python fallback
```

## Notes
- Base image must include nvcc (Dockerfile uses cuda:11.8.0-devel-ubuntu22.04).
- Keep CUDA pinned to 11.8 unless you plan a toolchain bump.

## Architecture

### C++ Extension
The custom op is implemented using PyTorch's C++ extension API:
- `csrc/fused_wave.cpp`: PyBind11 bindings that expose the op to Python
- `csrc/fused_wave_kernel.cu`: CUDA kernel implementation

### Python Interface
- `src/dredge/custom_ops/__init__.py`: Auto-loads compiled extension or falls back to Python
- `src/dredge/custom_ops/build.py`: Build helper for JIT compilation

### Testing
- `tests/test_custom_ops.py`: Validates the op matches reference implementation

## Development

### Building locally
If you have CUDA and nvcc installed:
```bash
cd /path/to/DREDGE-Cli
pip install -e .
```

### Testing
```bash
pytest tests/test_custom_ops.py -v
```

### Docker
The GPU build stage in the Dockerfile now uses `cuda:11.8.0-devel-ubuntu22.04` which includes nvcc:
```dockerfile
FROM nvidia/cuda:11.8.0-devel-ubuntu22.04 AS gpu-build
```

This ensures the custom ops are compiled when building the Docker image.
