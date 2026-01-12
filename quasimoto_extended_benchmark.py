import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# --- CREDITS ---
# Quasimoto Wave Function Architecture by: QueenFi703
# Extended with RFF baseline, visualization, and 4D support
# ----------------

class QuasimotoWave(nn.Module):
    """
    Author: QueenFi703
    Learnable continuous latent wave representation with controlled phase irregularity.
    """
    def __init__(self):
        super().__init__()
        self.A = nn.Parameter(torch.tensor(1.0))
        self.k = nn.Parameter(torch.randn(()))
        self.omega = nn.Parameter(torch.randn(()))
        self.v = nn.Parameter(torch.randn(()))
        self.log_sigma = nn.Parameter(torch.zeros(()))
        self.phi = nn.Parameter(torch.zeros(()))
        self.epsilon = nn.Parameter(torch.tensor(0.1))
        self.lmbda = nn.Parameter(torch.randn(()))

    def forward(self, x, t):
        sigma = torch.exp(self.log_sigma)
        phase = self.k * x - self.omega * t
        envelope = torch.exp(-0.5 * ((x - self.v * t) / sigma) ** 2)
        modulation = torch.sin(self.phi + self.epsilon * torch.cos(self.lmbda * x))
        
        # Real-only version for standard MSE benchmarking
        psi_real = self.A * torch.cos(phase) * envelope * modulation
        return psi_real

class QuasimotoWave4D(nn.Module):
    """
    Author: QueenFi703
    4D extension of QuasimotoWave for spatiotemporal volumetric data (x, y, z, t).
    Use cases: Medical imaging (4D CT/MRI), fluid dynamics, weather modeling.
    """
    def __init__(self):
        super().__init__()
        self.A = nn.Parameter(torch.tensor(1.0))
        # Wave numbers for each spatial dimension
        self.kx = nn.Parameter(torch.randn(()))
        self.ky = nn.Parameter(torch.randn(()))
        self.kz = nn.Parameter(torch.randn(()))
        self.omega = nn.Parameter(torch.randn(()))
        # Velocities for each spatial dimension
        self.vx = nn.Parameter(torch.randn(()))
        self.vy = nn.Parameter(torch.randn(()))
        self.vz = nn.Parameter(torch.randn(()))
        self.log_sigma = nn.Parameter(torch.zeros(()))
        self.phi = nn.Parameter(torch.zeros(()))
        self.epsilon = nn.Parameter(torch.tensor(0.1))
        # Modulation frequencies for each spatial dimension
        self.lmbda_x = nn.Parameter(torch.randn(()))
        self.lmbda_y = nn.Parameter(torch.randn(()))
        self.lmbda_z = nn.Parameter(torch.randn(()))

    def forward(self, x, y, z, t):
        sigma = torch.exp(self.log_sigma)
        # Phase propagation in 3D space
        phase = self.kx * x + self.ky * y + self.kz * z - self.omega * t
        # Gaussian envelope centered on moving point
        dx = x - self.vx * t
        dy = y - self.vy * t
        dz = z - self.vz * t
        envelope = torch.exp(-0.5 * ((dx**2 + dy**2 + dz**2) / sigma**2))
        # 3D phase modulation
        modulation = torch.sin(self.phi + 
                              self.epsilon * torch.cos(self.lmbda_x * x + 
                                                       self.lmbda_y * y + 
                                                       self.lmbda_z * z))
        psi_real = self.A * torch.cos(phase) * envelope * modulation
        return psi_real

class RandomFourierFeatures(nn.Module):
    """
    Random Fourier Features (RFF) baseline.
    Uses fixed random frequencies (not learned) for feature mapping.
    """
    def __init__(self, input_dim=1, num_features=256, sigma=10.0):
        super().__init__()
        # Fixed random frequencies (not learned)
        self.register_buffer('B', torch.randn(input_dim, num_features) * sigma)
        self.linear = nn.Linear(num_features * 2, 1)  # *2 for sin and cos
        
    def forward(self, x):
        # x: [N, input_dim]
        if x.dim() == 1:
            x = x.unsqueeze(-1)
        projections = x @ self.B  # [N, num_features]
        features = torch.cat([torch.sin(projections), torch.cos(projections)], dim=-1)
        return self.linear(features)

class SirenLayer(nn.Module):
    def __init__(self, in_f, out_f, w0=30.0, is_first=False):
        super().__init__()
        self.w0 = w0
        self.linear = nn.Linear(in_f, out_f)
        # Special initialization for SIREN
        with torch.no_grad():
            if is_first:
                self.linear.weight.uniform_(-1/in_f, 1/in_f)
            else:
                self.linear.weight.uniform_(-np.sqrt(6/in_f)/w0, np.sqrt(6/in_f)/w0)

    def forward(self, x):
        return torch.sin(self.w0 * self.linear(x))

class QuasimotoEnsemble(nn.Module):
    def __init__(self, n=16):
        super().__init__()
        self.waves = nn.ModuleList([QuasimotoWave() for _ in range(n)])
        self.head = nn.Linear(n, 1)
    
    def forward(self, x, t):
        feats = torch.stack([w(x, t) for w in self.waves], dim=-1)
        return self.head(feats)

class QuasimotoEnsemble4D(nn.Module):
    """4D ensemble for spatiotemporal data"""
    def __init__(self, n=8):
        super().__init__()
        self.waves = nn.ModuleList([QuasimotoWave4D() for _ in range(n)])
        self.head = nn.Linear(n, 1)
    
    def forward(self, x, y, z, t):
        feats = torch.stack([w(x, y, z, t) for w in self.waves], dim=-1)
        return self.head(feats)

# --- BENCHMARK TASK: The "Glitchy Chirp" ---
def generate_data():
    x = torch.linspace(-10, 10, 1000).view(-1, 1)
    t = torch.zeros_like(x)
    y = torch.sin(0.5 * x**2) * torch.exp(-0.1 * x**2)
    # The Glitch - positioned at 50-55% of the signal
    glitch_start = int(0.5 * len(x))
    glitch_end = int(0.55 * len(x))
    y[glitch_start:glitch_end] += 0.5 * torch.sin(20 * x[glitch_start:glitch_end])
    return x, t, y

def generate_4d_data(grid_size=20):
    """Generate 4D spatiotemporal data (3D space + time)"""
    # Create a smaller grid for 4D demo
    x = torch.linspace(-5, 5, grid_size)
    y = torch.linspace(-5, 5, grid_size)
    z = torch.linspace(-5, 5, grid_size)
    
    # Create meshgrid
    X, Y, Z = torch.meshgrid(x, y, z, indexing='ij')
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = Z.flatten()
    
    # Time snapshot
    t = torch.zeros_like(X_flat)
    
    # Generate a 3D Gaussian with some structure
    signal = torch.exp(-0.5 * (X_flat**2 + Y_flat**2 + Z_flat**2)) * \
             torch.sin(2 * X_flat) * torch.cos(2 * Y_flat) * torch.sin(2 * Z_flat)
    
    return X_flat, Y_flat, Z_flat, t, signal.unsqueeze(-1)

def train_model(model_name, model, x, t, y, epochs=2000, verbose=True):
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    losses = []
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        # Handle different input signatures
        try:
            # Try (x, t) signature first (for Quasimoto)
            pred = model(x.squeeze(), t.squeeze()).view(-1, 1)
        except TypeError:
            # Fall back to (x) signature (for SIREN/RFF)
            pred = model(x)
            
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
        
        if verbose and epoch % 500 == 0:
            print(f"[{model_name}] Epoch {epoch} Loss: {loss.item():.6f}")
    
    return loss.item(), losses

def train_model_4d(model_name, model, x, y_coord, z, t, signal, epochs=1000, verbose=True):
    """Training function for 4D models"""
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    losses = []
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(x, y_coord, z, t).view(-1, 1)
        loss = criterion(pred, signal)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
        
        if verbose and epoch % 200 == 0:
            print(f"[{model_name}] Epoch {epoch} Loss: {loss.item():.6f}")
    
    return loss.item(), losses

def visualize_predictions(x, y_true, models, model_names, save_path='quasimoto_comparison.png'):
    """Plot true signal vs model predictions"""
    fig, axes = plt.subplots(len(models) + 1, 1, figsize=(14, 3 * (len(models) + 1)))
    
    if len(models) == 0:
        axes = [axes]
    
    # Plot ground truth
    axes[0].plot(x.numpy(), y_true.numpy(), 'k-', linewidth=2, label='Ground Truth')
    axes[0].set_title('Ground Truth Signal', fontsize=14, fontweight='bold')
    axes[0].legend(fontsize=11)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlabel('x')
    axes[0].set_ylabel('y')
    
    # Plot predictions
    for idx, (model, name) in enumerate(zip(models, model_names)):
        with torch.no_grad():
            if name.startswith("Quasimoto"):
                pred = model(x.squeeze(), torch.zeros_like(x.squeeze())).view(-1, 1)
            else:
                pred = model(x)
        
        # Calculate residual
        residual = (y_true - pred).numpy()
        mse = np.mean(residual**2)
        
        axes[idx + 1].plot(x.numpy(), y_true.numpy(), 'k--', alpha=0.3, linewidth=1, label='Ground Truth')
        axes[idx + 1].plot(x.numpy(), pred.numpy(), 'r-', linewidth=2, label=f'{name} Prediction')
        axes[idx + 1].set_title(f'{name} Fit (MSE: {mse:.8f})', fontsize=14, fontweight='bold')
        axes[idx + 1].legend(fontsize=11)
        axes[idx + 1].grid(True, alpha=0.3)
        axes[idx + 1].set_xlabel('x')
        axes[idx + 1].set_ylabel('y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Visualization saved to {save_path}")
    return fig

def visualize_convergence(losses_dict, save_path='quasimoto_convergence.png'):
    """Plot convergence curves for all models"""
    plt.figure(figsize=(12, 6))
    
    for name, losses in losses_dict.items():
        plt.plot(losses, label=name, linewidth=2)
    
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('MSE Loss', fontsize=12)
    plt.title('Training Convergence Comparison', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✓ Convergence plot saved to {save_path}")

# Execution
if __name__ == "__main__":
    print("=" * 70)
    print("QUASIMOTO EXTENDED BENCHMARK")
    print("=" * 70)
    print("\n1D Benchmark: Glitchy Chirp Signal\n")
    
    x, t, y = generate_data()
    
    # Initialize models
    print("Initializing models...")
    quasimoto_net = QuasimotoEnsemble(n=16)
    siren_net = nn.Sequential(
        SirenLayer(1, 64, is_first=True),
        SirenLayer(64, 64),
        nn.Linear(64, 1)
    )
    rff_net = RandomFourierFeatures(input_dim=1, num_features=128, sigma=5.0)
    
    print("✓ Models initialized\n")
    
    # Train models
    print("-" * 70)
    print("Training 1D Models (2000 epochs each)")
    print("-" * 70)
    
    models = [quasimoto_net, siren_net, rff_net]
    model_names = ["Quasimoto", "SIREN", "RFF"]
    losses_dict = {}
    final_losses = []
    
    for model, name in zip(models, model_names):
        print(f"\n{name}:")
        final_loss, losses = train_model(name, model, x, t, y, epochs=2000)
        losses_dict[name] = losses
        final_losses.append(final_loss)
    
    # Print results
    print("\n" + "=" * 70)
    print("FINAL RESULTS - 1D Benchmark")
    print("=" * 70)
    for name, loss in zip(model_names, final_losses):
        print(f"{name:20s} Final Loss: {loss:.8f}")
    
    # Generate visualizations
    print("\n" + "-" * 70)
    print("Generating Visualizations...")
    print("-" * 70)
    visualize_predictions(x, y, models, model_names)
    visualize_convergence(losses_dict)
    
    # 4D Benchmark
    print("\n" + "=" * 70)
    print("4D BENCHMARK: Spatiotemporal Volumetric Data")
    print("=" * 70)
    print("\nGenerating 4D data (20x20x20 grid = 8000 points)...")
    
    X, Y, Z, T, signal = generate_4d_data(grid_size=20)
    print(f"✓ 4D data generated: {len(X)} points")
    
    print("\nTraining 4D Quasimoto Ensemble (1000 epochs)...")
    quasimoto_4d = QuasimotoEnsemble4D(n=8)
    final_loss_4d, losses_4d = train_model_4d("Quasimoto-4D", quasimoto_4d, 
                                                X, Y, Z, T, signal, 
                                                epochs=1000)
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS - 4D Benchmark")
    print("=" * 70)
    print(f"Quasimoto-4D Final Loss: {final_loss_4d:.8f}")
    
    # Plot 4D convergence
    plt.figure(figsize=(10, 5))
    plt.plot(losses_4d, linewidth=2, color='purple')
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('MSE Loss', fontsize=12)
    plt.title('Quasimoto-4D Training Convergence', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.tight_layout()
    plt.savefig('quasimoto_4d_convergence.png', dpi=150, bbox_inches='tight')
    print("✓ 4D convergence plot saved to quasimoto_4d_convergence.png")
    
    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  • quasimoto_comparison.png - Model predictions comparison")
    print("  • quasimoto_convergence.png - Training convergence curves")
    print("  • quasimoto_4d_convergence.png - 4D model convergence")
