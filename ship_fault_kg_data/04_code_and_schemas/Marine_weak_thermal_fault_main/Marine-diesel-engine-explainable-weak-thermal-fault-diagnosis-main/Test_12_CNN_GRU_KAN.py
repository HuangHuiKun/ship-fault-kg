import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Import data interface (Ensure this path is correct in your project structure)
from Code.Test_12_1 import read_data


# ======================================================================================================================
# 1. KAN (Kolmogorov-Arnold Network) Layer Implementation
# Reference: Section 2.2.3 - Replacing MLP classifiers with KAN
# Core Formulation: phi(x) = w_b * b(x) + w_s * spline(x)
# ======================================================================================================================
class KANLayer(nn.Module):
    """
    Simplified implementation of a Kolmogorov-Arnold Network (KAN) Layer.

    Mechanism:
    Instead of fixed activation functions on nodes (like MLP), KANs learn activation functions on edges.
    Here, we approximate the learnable function using:
    1. Base Function b(x): SiLU (Sigmoid Linear Unit).
    2. Spline Function: Approximated via a non-linear transformation (e.g., Sine) with learnable weights.
    """

    def __init__(self, in_features, out_features, grid_size=5):
        super(KANLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features

        # Base weights for the linear transformation of the activation
        self.base_weight = nn.Parameter(torch.Tensor(out_features, in_features))

        # Spline weights for the non-linear learnable part
        self.spline_weight = nn.Parameter(torch.Tensor(out_features, in_features))

        # Learnable scaling factor for the layer output
        self.scale = nn.Parameter(torch.ones(1))

        self.reset_parameters()

    def reset_parameters(self):
        """Initialize weights using Kaiming Uniform initialization."""
        nn.init.kaiming_uniform_(self.base_weight, a=np.sqrt(5))
        nn.init.constant_(self.spline_weight, 0.1)

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, in_features).
        Returns:
            torch.Tensor: Output tensor of shape (batch_size, out_features).
        """
        # 1. Base Component: w_b * silu(x)
        # Corresponds to Eq. 12 in the manuscript where b(x) = silu(x)
        base_output = F.linear(F.silu(x), self.base_weight)

        # 2. Spline Component: w_s * spline(x)
        # Simplified here as w_s * sin(x) to simulate periodic/non-linear behavior efficiently
        # without requiring complex B-Spline CUDA compilation.
        spline_output = F.linear(torch.sin(x), self.spline_weight)

        # 3. Aggregation with scaling
        return (base_output + spline_output) * self.scale


class KANClassifier(nn.Module):
    """
    KAN-based Classifier Module.
    Structure: Input -> KAN Layer 1 -> KAN Layer 2 -> Output Logits
    """

    def __init__(self, in_dim, hidden_dim, num_classes):
        super(KANClassifier, self).__init__()
        self.layer1 = KANLayer(in_dim, hidden_dim)
        self.layer2 = KANLayer(hidden_dim, num_classes)
        # Note: Softmax is implicitly handled by CrossEntropyLoss during training.

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        return x


# ======================================================================================================================
# 2. CNN_GRU_KAN Model Definition
# Architecture Reference: Fig. 3 - Hybrid CNN-GRU-KAN Framework
# ======================================================================================================================
class PNCOFD(nn.Module):
    """
    Petri Net-Based Co-Evolutionary Optimization for Fault Diagnosis (PNCOFD) Model.

    This hybrid architecture consists of three stages:
    1. CNN: Spatial feature extraction from sensor matrices.
    2. GRU: Temporal feature modeling.
    3. KAN: Non-linear classification.
    """

    def __init__(self, num_classes=11):
        super(PNCOFD, self).__init__()

        # --- A. Spatial Feature Extraction (CNN) ---
        # Input Shape: (Batch, 1, 3, 4) -> Based on 12 thermal parameters reshaped to 3x4
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.LeakyReLU(0.2),  # LeakyReLU used as per pre-training specifications

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2),
            # Note: Pooling is skipped due to the small input resolution (3x4).
        )

        # CNN Output Dimension Calculation:
        # Output channels (32) * Height (3) * Width (4) = 384
        self.cnn_out_dim = 384

        # --- B. Temporal Feature Modeling (GRU) ---
        # We treat the flattened CNN features as a sequence for the GRU.
        self.gru_input_dim = self.cnn_out_dim
        self.gru_hidden_dim = 100  # As specified in Table 3 of the manuscript

        self.gru = nn.GRU(
            input_size=self.gru_input_dim,
            hidden_size=self.gru_hidden_dim,
            num_layers=1,
            batch_first=True
        )

        # --- C. Classification (KAN) ---
        # Innovation: Replacing standard MLP with KAN for better non-linear interpretability.
        self.classifier = KANClassifier(
            in_dim=self.gru_hidden_dim,
            hidden_dim=64,
            num_classes=num_classes
        )

    def forward(self, x):
        # 1. Spatial Extraction
        x = self.cnn(x)  # Shape: (Batch, 32, 3, 4)
        x = x.view(x.size(0), -1)  # Flatten -> (Batch, 384)

        # 2. Temporal Modeling
        # Reshape to (Batch, Seq_Len=1, Features) for GRU
        x = x.unsqueeze(1)
        x, _ = self.gru(x)
        # Extract the last time step output
        x = x[:, -1, :]  # Shape: (Batch, 100)

        # 3. Classification
        logits = self.classifier(x)  # Shape: (Batch, Num_Classes)
        return logits


# ======================================================================================================================
# 3. Transfer Learning Strategy S8
# Reference: Table 11 & Section 2.3.3
# Strategy S8: Freeze CNN layers, Fine-tune GRU and KAN layers.
# ======================================================================================================================
def get_transfer_strategy_S8(model):
    """
    Applies Transfer Learning Strategy S8.

    Mechanism:
    - Freezes the spatial feature extractor (CNN) to retain source domain knowledge.
    - Unfreezes the temporal (GRU) and classifier (KAN) modules to adapt to the target domain.
    """
    # 1. Freeze CNN (Feature Extractor)
    for param in model.cnn.parameters():
        param.requires_grad = False

    # 2. Unfreeze GRU (Temporal Adapter)
    for param in model.gru.parameters():
        param.requires_grad = True

    # 3. Unfreeze Classifier (Decision Boundary)
    for param in model.classifier.parameters():
        param.requires_grad = True

    return model


# ======================================================================================================================
# 4. Training and Validation Loop
# ======================================================================================================================
def train_epoch(model, loader, criterion, optimizer, device):
    """Standard training loop for one epoch."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for inputs, labels in loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    return total_loss / len(loader), 100 * correct / total


def main():
    # 1. Data Loading
    print("Step 1: Loading Data...")
    # Assuming read_data returns DataLoaders for Source (train) and Target (val/test) domains
    train_loader, val_loader, test_loader = read_data()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ==================================================================================================================
    # Phase 1: Pre-training on Source Domain
    # ==================================================================================================================
    print("\n>>> Phase 1: Pre-training CNN_GRU_KAN on Source Domain...")
    model = PNCOFD(num_classes=11).to(device)
    criterion = nn.CrossEntropyLoss()

    # Optimizer settings as per Table 3 (LR=0.001)
    optimizer_pre = optim.Adam(model.parameters(), lr=0.001)

    pretrain_epochs = 15
    pre_loss_history = []

    for epoch in range(pretrain_epochs):
        loss, acc = train_epoch(model, train_loader, criterion, optimizer_pre, device)
        pre_loss_history.append(loss)
        if (epoch + 1) % 5 == 0:
            print(f"[Pre-train] Epoch {epoch + 1}/{pretrain_epochs} | Loss: {loss:.4f} | Acc: {acc:.2f}%")

    # ==================================================================================================================
    # Phase 2: Transfer Learning (Strategy S8)
    # ==================================================================================================================
    print("\n>>> Phase 2: Applying Transfer Strategy S8 (Freeze CNN, FT GRU+KAN)...")

    # Apply Strategy S8: Freeze CNN weights
    model = get_transfer_strategy_S8(model)

    # Filter parameters to only update those with requires_grad=True
    params_to_update = filter(lambda p: p.requires_grad, model.parameters())

    # Fine-tuning typically uses a lower or same learning rate. Here set to 0.0005 for stability.
    optimizer_ft = optim.Adam(params_to_update, lr=0.0005)

    ft_epochs = 20
    ft_loss_history = []

    print(f"Fine-tuning on Target Domain (Validation Set)...")
    for epoch in range(ft_epochs):
        # Note: We use val_loader here to simulate the Target Domain training data (Few-shot scenario)
        loss, acc = train_epoch(model, val_loader, criterion, optimizer_ft, device)
        ft_loss_history.append(loss)
        if (epoch + 1) % 5 == 0:
            print(f"[Fine-tune] Epoch {epoch + 1}/{ft_epochs} | Loss: {loss:.4f} | Acc: {acc:.2f}%")

    # ==================================================================================================================
    # Phase 3: Final Testing
    # ==================================================================================================================
    print("\n>>> Phase 3: Final Testing on Target Domain (Test Set)...")
    model.eval()
    test_correct = 0
    test_total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            test_total += labels.size(0)
            test_correct += (predicted == labels).sum().item()

    print(f"Final Test Accuracy (Strategy S8): {100 * test_correct / test_total:.2f}%")

    # --- Visualization ---
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, pretrain_epochs + 1), pre_loss_history, label='Source Pre-training')
    plt.plot(range(pretrain_epochs + 1, pretrain_epochs + ft_epochs + 1), ft_loss_history,
             label='Target Fine-tuning (S8)')
    plt.axvline(x=pretrain_epochs, color='r', linestyle='--', label='Transfer Point')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Training Loss Trajectory (Strategy S8)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()


if __name__ == '__main__':
    main()