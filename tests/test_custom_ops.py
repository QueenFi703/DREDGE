import torch
from dredge.custom_ops import fused_wave


def test_fused_wave_matches_python():
    x = torch.randn(4, device="cuda" if torch.cuda.is_available() else "cpu")
    y = fused_wave(x, alpha=0.3)
    # Reference
    y_ref = 0.3 * x.sin() + 0.7 * x
    assert torch.allclose(y, y_ref, atol=1e-5, rtol=1e-5)


def test_fused_wave_default_alpha():
    x = torch.randn(10, device="cuda" if torch.cuda.is_available() else "cpu")
    y = fused_wave(x)
    # Reference with default alpha=0.5
    y_ref = 0.5 * x.sin() + 0.5 * x
    assert torch.allclose(y, y_ref, atol=1e-5, rtol=1e-5)


def test_fused_wave_different_shapes():
    # Test with 2D tensor
    x = torch.randn(4, 8, device="cuda" if torch.cuda.is_available() else "cpu")
    y = fused_wave(x, alpha=0.2)
    y_ref = 0.2 * x.sin() + 0.8 * x
    assert torch.allclose(y, y_ref, atol=1e-5, rtol=1e-5)
