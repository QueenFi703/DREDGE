import os
from torch.utils.cpp_extension import load


def build_extensions():
    this_dir = os.path.dirname(__file__)
    sources = [
        os.path.join(this_dir, "..", "..", "..", "csrc", "fused_wave.cpp"),
        os.path.join(this_dir, "..", "..", "..", "csrc", "fused_wave_kernel.cu"),
    ]
    return load(
        name="dredge_custom_ops",
        sources=sources,
        extra_cuda_cflags=["-lineinfo"],
        verbose=False,
    )


if __name__ == "__main__":
    build_extensions()
