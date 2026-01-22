#include <torch/extension.h>

torch::Tensor fused_wave_cuda(torch::Tensor x, double alpha) {
    // minimal example: y = alpha * sin(x) + (1 - alpha) * x
    auto y = alpha * x.sin() + (1.0 - alpha) * x;
    return y;
}
