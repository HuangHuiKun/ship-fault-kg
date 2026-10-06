import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Import data interface
from Code.Test_12_1 import read_data


# ======================================================================================================================
# 1. WCL Network Structure Definition
# Reference: Zhang et al., "Wide Convolutional Learning for Misfire Detection", Measurement, 2024.
# ======================================================================================================================
class WCL(nn.Module):
    """
    Wide Convolutional Learning (WCL) Network.

    Architecture Highlights:
    1. Wide Convolution Block: Uses larger kernels (or mimics them) to capture global features and resist noise.
    2. Deep Convolution Blocks: Extracts high-level abstractions.
    3. LSTM Layer: Models temporal dependencies in the flattened feature sequence.
    """

    def __init__(self, num_classes=11):
        super(WCL, self).__init__()

        # --- Block 1: Wide Convolution Equivalent ---
        # Feature: Uses a 3x3 kernel on a 3x4 input to cover nearly the entire receptive field.
        # This mimics the "Wide Kernel" effect described in the literature for noise robustness.
        self.block1 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=(3, 3), stride=1, padding=1),
            nn.BatchNorm2d(16),
            nn.LeakyReLU(0.2, inplace=True),  # LeakyReLU as specified in
            # Note: Pooling is skipped to preserve spatial information for small inputs.
        )

        # --- Block 2: Deep Convolution ---
        self.block2 = nn.Sequential(
            nn.Conv2d(16, 32, kernel_size=(2, 2), stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # --- Block 3: Deep Convolution ---
        self.block3 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=(2, 2), stride=1, padding=0),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # --- Feature Adaptation for LSTM ---
        # The CNN output needs to be reshaped into a sequence format (Batch, Seq, Feature) for LSTM.
        # We use Adaptive Pooling to force the spatial dimension to (1, 4), simulating a sequence length of 4.
        self.adapter_pool = nn.AdaptiveAvgPool2d((1, 4))

        # --- Block 5: LSTM Layer ---
        # Captures temporal dynamics from the spatial sequence
        # Input Size: 64 (Channels), Hidden Size: 128
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=128,
            num_layers=2,
            batch_first=True
        )

        # --- Classifier ---
        # Structure: FC -> Softmax
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 100),  # Takes the output of the last time step
            nn.BatchNorm1d(100),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Dropout(0.5),  # Regularization
            nn.Linear(100, num_classes)
        )

    def forward(self, x):
        """
        Forward pass logic.
        Args:
            x (torch.Tensor): Input tensor of shape (Batch, 1, 3, 4).
        """
        # 1. Spatial Feature Extraction
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)

        # 2. Sequence Formation
        # Transform (Batch, Channels, Height, Width) -> (Batch, Time, Features)
        # We treat the width dimension (4) as the time sequence and channels (64) as features.
        x = self.adapter_pool(x)  # Shape: (B, 64, 1, 4)
        x = x.squeeze(2)  # Shape: (B, 64, 4)
        x = x.permute(0, 2, 1)  # Shape: (B, 4, 64) -> (Batch, Time, Feat)

        # 3. Temporal Modeling (LSTM)
        # lstm_out: (Batch, Seq_Len, Hidden_Size)
        lstm_out, _ = self.lstm(x)

        # Use the output from the last time step for classification
        last_step_out = lstm_out[:, -1, :]  # Shape: (Batch, 128)

        # 4. Classification
        logits = self.classifier(last_step_out)
        return logits


# ======================================================================================================================
# 2. Transfer Learning Utilities
# ======================================================================================================================
def freeze_layers(model, freeze_conv=True):
    """
    Applies the freezing strategy for transfer learning.

    Strategy:
    - Freeze low-level feature extractors (Convolutional Blocks).
    - Fine-tune high-level decision layers (LSTM + Classifier).
    Ref:
    """
    if freeze_conv:
        for name, param in model.named_parameters():
            # Freeze parameters in Block 1, 2, and 3
            if "block" in name:
                param.requires_grad = False
            else:
                param.requires_grad = True
    return model


# ======================================================================================================================
# 3. Training and Transfer Pipeline
# ======================================================================================================================
def train_model(model, loader, criterion, optimizer, device, epochs=10, phase="Pre-training"):
    """Generic training loop."""
    model.train()
    loss_history = []

    print(f"--- Starting {phase} ---")
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        avg_loss = running_loss / len(loader)
        acc = 100 * correct / total
        loss_history.append(avg_loss)
        print(f"[{phase}] Epoch {epoch + 1}/{epochs} | Loss: {avg_loss:.4f} | Acc: {acc:.2f}%")

    return loss_history


def main():
    # 1. Data Loading
    print("Reading Data...")
    train_loader, val_loader, test_loader = read_data()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = 11

    # 2. Model Initialization
    model = WCL(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()

    # ==================================================================================================================
    # Phase 1: Source Domain Pre-training
    # Assumption: train_loader contains Source Domain data (Large scale).
    # ==================================================================================================================
    # Use a standard learning rate for pre-training
    optimizer_pre = optim.Adam(model.parameters(), lr=0.001)

    pretrain_losses = train_model(
        model, train_loader, criterion, optimizer_pre, device,
        epochs=20, phase="Source Pre-training"
    )

    # ==================================================================================================================
    # Phase 2: Target Domain Transfer (Fine-tuning)
    # Assumption: val_loader contains Target Domain data (Few-shot / Different operating condition).
    # ==================================================================================================================
    print("\nApplying Transfer Learning Strategy...")

    # Step A: Freeze Convolutional Layers
    model = freeze_layers(model, freeze_conv=True)

    # Step B: Fine-tune using a lower learning rate
    # Filter only parameters that require gradients
    params_to_update = filter(lambda p: p.requires_grad, model.parameters())
    optimizer_ft = optim.Adam(params_to_update, lr=0.0001)

    finetune_losses = train_model(
        model, val_loader, criterion, optimizer_ft, device,
        epochs=15, phase="Target Fine-tuning"
    )

    # ==================================================================================================================
    # Phase 3: Final Testing
    # Evaluation on the Target Domain Test Set.
    # ==================================================================================================================
    print("\n--- Final Testing on Target Domain ---")
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f"Final Test Accuracy: {100 * correct / total:.2f}%")

    # --- Visualization ---
    plt.figure(figsize=(10, 5))
    # Plot Pre-training Loss
    plt.plot(pretrain_losses, label='Source Pre-training Loss')
    # Plot Fine-tuning Loss (concatenated)
    plt.plot(range(len(pretrain_losses), len(pretrain_losses) + len(finetune_losses)),
             finetune_losses, label='Target Fine-tuning Loss')

    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('WCL Transfer Learning Trajectory')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()


if __name__ == '__main__':
    main()