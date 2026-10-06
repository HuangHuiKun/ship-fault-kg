import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from Code.Test_12 import DPFD_ACAM_ISimAM_TwoChannelFusion
from Code.Test_12_4_1 import RIME  # Import the RIME algorithm implementation
from Code.Test_12_1 import read_data


# ======================================================================================================================
# ---------- 1. Parameter Mapping Functions ----------
# RIME produces values in the continuous range [0, 1].
# These functions map them to the discrete/continuous hyperparameter space.
# ======================================================================================================================

def map_learning_rate(x):
    """Maps [0, 1] to learning rate range [1e-5, 5e-2]."""
    return 1e-5 + x * (5e-2 - 1e-5)


def map_batch_size(x):
    """
    Maps [0, 1] to batch size range [16, 128].
    Ensures the output is a multiple of 8 for hardware efficiency.
    """
    min_bs, max_bs = 16, 128
    val = min_bs + x * (max_bs - min_bs)
    val = int(round(val / 8) * 8)  # Quantize to nearest multiple of 8
    # Clip to valid range just in case
    return max(min_bs, min(val, max_bs))


def map_DPFD_channels(x):
    """
    Maps [0, 1] to convolution channel range [32, 256].
    Ensures the output is a multiple of 16.
    """
    min_ch, max_ch = 32, 256
    val = int(round(min_ch + x * (max_ch - min_ch)))
    val = int(round(val / 16) * 16)
    return max(min_ch, min(val, max_ch))


def map_ACAM_reduction(x):
    """Maps [0, 1] to CBAM reduction ratio range [2, 16]."""
    min_r, max_r = 2, 16
    val = int(round(min_r + x * (max_r - min_r)))
    return max(1, val)


def decode_params(param_vector):
    """Decodes the normalized vector from CRIME into actual hyperparameters."""
    lr = map_learning_rate(param_vector[0])
    batch_size = map_batch_size(param_vector[1])
    conv_channels = map_DPFD_channels(param_vector[2])
    cbam_reduction = map_ACAM_reduction(param_vector[3])
    return lr, batch_size, conv_channels, cbam_reduction


# ======================================================================================================================
# ---------- 2. Training and Evaluation Interfaces ----------
# ======================================================================================================================

def train_one_epoch(model, dataloader, optimizer, device):
    """Performs one epoch of training."""
    model.train()
    loss_fn = nn.CrossEntropyLoss()
    for x, y in dataloader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = loss_fn(out, y)
        loss.backward()
        optimizer.step()


def evaluate(model, dataloader, device):
    """Computes simple accuracy."""
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            pred = out.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return correct / total if total > 0 else 0


def evaluate_loss_and_acc(model, dataloader, device, criterion):
    """Computes both average loss and accuracy."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            outputs = model(x)
            loss = criterion(outputs, y)
            total_loss += loss.item() * x.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(y).sum().item()
            total += y.size(0)
    avg_loss = total_loss / total
    accuracy = correct / total
    return avg_loss, accuracy


# ======================================================================================================================
# ---------- 3. Fitness Function (Optimization Objective) ----------
# ======================================================================================================================

def fitness(param_vector):
    """
    Evaluates a specific set of hyperparameters.

    Process:
    1. Decode normalized parameters to actual values (lr, batch_size, etc.).
    2. Load data and initialize model with these parameters.
    3. Train for a fixed number of epochs (e.g., 50).
    4. Return negative accuracy (since RIME minimizes the objective).
    """
    lr, batch_size, conv_channels, cbam_reduction = decode_params(param_vector)

    # 1. Data Loading (Batch size affects the loader)
    train_loader, val_loader, test_loader = read_data(batch_size)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 2. Model Initialization (Channels/Reduction ratio affect structure)
    model = DPFD_ACAM_ISimAM_TwoChannelFusion(conv_channels=conv_channels, cbam_reduction=cbam_reduction)
    model.to(device)

    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # 3. Short Training Loop (Proxy Task)
    # Train for 50 epochs to estimate performance.
    # Increase this for more accurate (but slower) results.
    for epoch in range(50):
        train_one_epoch(model, train_loader, optimizer, device)

    # 4. Evaluation
    train_loss, train_acc = evaluate_loss_and_acc(model, train_loader, device, criterion)
    val_loss, val_acc = evaluate_loss_and_acc(model, val_loader, device, criterion)
    test_loss, test_acc = evaluate_loss_and_acc(model, test_loader, device, criterion)

    # Logging current trial
    print(f"[Hyperparam Eval] LR={lr:.5f}, Batch={batch_size}, Ch={conv_channels}, Red={cbam_reduction}")
    print(f"   Train: Loss={train_loss:.4f}, Acc={train_acc:.4f} | "
          f"Val: Loss={val_loss:.4f}, Acc={val_acc:.4f} | "
          f"Test: Loss={test_loss:.4f}, Acc={test_acc:.4f}")

    # Objective: Minimize negative accuracy (Maximize accuracy)
    return -test_acc


# ======================================================================================================================
# ---------- 4. Main Execution: RIME Optimization ----------
# ======================================================================================================================
if __name__ == "__main__":
    dim = 4  # Number of hyperparameters to optimize
    pop_size = 20  # Population size (Number of agents)
    iters = 30  # Maximum iterations

    print(f"Starting RIME Optimization with Population={pop_size}, Iterations={iters}...")

    # Initialize RIME optimizer
    rime = RIME(fitness_func=fitness, dim=dim, pop_size=pop_size, max_iter=iters)

    # Run optimization
    best_params, best_fitness = rime.optimize()

    # Decode and Display Results
    best_acc = -best_fitness
    best_lr, best_bs, best_ch, best_red = decode_params(best_params)

    print("\n" + "=" * 50)
    print("Optimization Completed.")
    print("=" * 50)
    print(f"Best Hyperparameters:")
    print(f"  - Learning Rate:    {best_lr:.5f}")
    print(f"  - Batch Size:       {best_bs}")
    print(f"  - Conv Channels:    {best_ch}")
    print(f"  - CBAM Reduction:   {best_red}")
    print(f"Best Test Accuracy:   {best_acc:.4f}")
    print("=" * 50)