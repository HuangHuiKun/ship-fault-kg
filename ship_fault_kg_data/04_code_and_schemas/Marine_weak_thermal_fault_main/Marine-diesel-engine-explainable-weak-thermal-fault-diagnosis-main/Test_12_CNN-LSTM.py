import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Import data interface
from Code.Test_12_1 import read_data


# ======================================================================================================================
# 1. Residual Denoising Module
# Reference: Qin et al., "Anti-noise diesel engine misfire diagnosis..." (2023)
# Function: Learns the noise distribution F(y) to recover the clean signal x = y - F(y).
# ======================================================================================================================
class ResidualDenoisingModule(nn.Module):
    """
    Residual-CNN Denoising Module.

    Mathematical Formulation:
        Let y be the noisy input and x be the clean signal.
        The module learns a mapping F(y) approx Noise.
        The denoised output is calculated as: x_clean = y - F(y).
    """

    def __init__(self):
        super(ResidualDenoisingModule, self).__init__()
        # Input Shape: (Batch, 1, 3, 4)

        # Feature extraction for noise estimation
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(16, 16, kernel_size=3, padding=1)

        # Output layer: Predicts the noise map (1 channel)
        self.conv3 = nn.Conv2d(16, 1, kernel_size=3, padding=1)

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): Noisy input tensor y.
        Returns:
            denoised_signal (torch.Tensor): Estimated clean signal (y - noise).
            predicted_noise (torch.Tensor): Estimated noise map F(y).
        """
        out = self.relu(self.conv1(x))
        out = self.relu(self.conv2(out))

        # Predicted noise component F(y)
        predicted_noise = self.conv3(out)

        # Residual connection: Subtract noise from input
        denoised_signal = x - predicted_noise

        return denoised_signal, predicted_noise


# ======================================================================================================================
# 2. MSCNN-LSTM Network Architecture
# Structure: Denoising -> Multi-Scale Feature Extraction -> Temporal Modeling -> Classification
# ======================================================================================================================
class MultiScaleCNN_LSTM(nn.Module):
    """
    Multi-Scale Convolutional Neural Network with LSTM (MSCNN-LSTM).

    Components:
    1. Residual Denoising Module: Pre-processing for noise robustness.
    2. Multi-Scale CNN: Captures features at different receptive fields (1x1, 3x3, anisotropic).
    3. LSTM: Models temporal dependencies in the feature sequence.
    """

    def __init__(self, num_classes=11):
        super(MultiScaleCNN_LSTM, self).__init__()

        # --- Module 1: Denoising ---
        self.denoising_module = ResidualDenoisingModule()

        # --- Module 2: Multi-Scale Feature Extraction ---
        # Branch 1: Small receptive field (1x1) for local details
        self.branch1 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=1, padding=0),
            nn.BatchNorm2d(16),
            nn.ReLU(),
        )
        # Branch 2: Medium receptive field (3x3) for spatial context
        self.branch2 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
        )
        # Branch 3: Anisotropic receptive field (3x1) for directional features
        self.branch3 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=(3, 1), padding=(1, 0)),
            nn.BatchNorm2d(16),
            nn.ReLU(),
        )

        # Feature Fusion Dimension: 16 (Branch1) + 16 (Branch2) + 16 (Branch3) = 48 Channels
        self.pool = nn.MaxPool2d(kernel_size=2)  # Downsampling: 3x4 -> 1x2

        # --- Module 3: Sequence Modeling (LSTM) ---
        # Flatten dimension calculation:
        # Input (1, 3, 4) -> Convs (48, 3, 4) -> Pool (48, 1, 2) -> Flatten (48 * 1 * 2 = 96)
        self.flatten_dim = 48 * 1 * 2
        self.lstm_input_size = 64

        # Adapter to reduce dimensions before LSTM
        self.adapter = nn.Linear(self.flatten_dim, self.lstm_input_size)

        self.lstm = nn.LSTM(
            input_size=self.lstm_input_size,
            hidden_size=64,
            num_layers=2,
            batch_first=True
        )

        # --- Module 4: Classifier ---
        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        # 1. Denoising Stage
        # x_clean: Denoised features used for classification
        # predicted_noise: Used for auxiliary loss calculation
        x_clean, predicted_noise = self.denoising_module(x)

        # 2. Multi-Scale Extraction Stage
        f1 = self.branch1(x_clean)
        f2 = self.branch2(x_clean)
        f3 = self.branch3(x_clean)

        # Feature Concatenation along channel dimension
        feat = torch.cat([f1, f2, f3], dim=1)  # Shape: (Batch, 48, 3, 4)
        feat = self.pool(feat)  # Shape: (Batch, 48, 1, 2)

        # 3. Temporal Modeling Stage
        # Reshape to (Batch, Features)
        feat = feat.view(feat.size(0), -1)  # Shape: (Batch, 96)
        feat = self.adapter(feat)  # Shape: (Batch, 64)

        # Add sequence dimension: (Batch, Seq_Len=1, Features)
        feat = feat.unsqueeze(1)

        lstm_out, _ = self.lstm(feat)  # Shape: (Batch, 1, 64)
        lstm_out = lstm_out[:, -1, :]  # Take last time step

        # 4. Classification Stage
        logits = self.classifier(lstm_out)

        return logits, predicted_noise


# ======================================================================================================================
# 3. Training Pipeline (Multi-Task Learning)
# ======================================================================================================================

def train_mscnn_lstm():
    # 1. Data Loading
    print("Loading datasets...")
    train_loader, val_loader, test_loader = read_data()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Initializing MSCNN-LSTMNet on {device}...")

    model = MultiScaleCNN_LSTM(num_classes=11).to(device)

    # Optimization Setup
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Loss Functions
    criterion_cls = nn.CrossEntropyLoss()  # For Classification
    criterion_mse = nn.MSELoss()  # For Denoising (Reconstruction)

    # Hyperparameters
    epochs = 30
    lambda_noise = 0.5  # Weight for the denoising auxiliary loss
    noise_std = 0.3  # Standard deviation for synthetic noise injection

    train_losses = []

    print("Starting Training...")

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            # --- Self-Supervised Denoising Task Setup ---
            # To train the denoising module, we artificially corrupt the clean input.
            # Noisy Input = Clean Input + Gaussian Noise
            noise = torch.randn_like(inputs) * noise_std
            noisy_inputs = inputs + noise
            target_noise = noise  # The model tries to predict this noise

            # Forward Pass (using Noisy Inputs)
            outputs, pred_noise = model(noisy_inputs)

            # --- Multi-Task Loss Calculation ---
            # Task 1: Classification Loss (Robustness)
            loss_c = criterion_cls(outputs, labels)

            # Task 2: Denoising Loss (MSE between predicted and actual noise)
            loss_n = criterion_mse(pred_noise, target_noise)

            # Total Loss
            loss = loss_c + lambda_noise * loss_n

            # Backward Pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

            # Accuracy Metric
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        # Logging
        avg_loss = running_loss / len(train_loader)
        acc = 100 * correct / total
        train_losses.append(avg_loss)

        print(f"Epoch [{epoch + 1}/{epochs}] | Total Loss: {avg_loss:.4f} | Train Acc: {acc:.2f}%")

    # ==================================================================================================================
    # 4. Testing & Visualization
    # ==================================================================================================================
    print("\nStarting Evaluation...")
    model.eval()
    test_acc = 0
    test_total = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            # Note: During testing, we can input either clean or noisy data to test robustness.
            # Here we test on the standard test set.
            outputs, _ = model(inputs)
            _, predicted = torch.max(outputs.data, 1)

            test_total += labels.size(0)
            test_acc += (predicted == labels).sum().item()

    print(f"Final Test Accuracy: {100 * test_acc / test_total:.2f}%")

    # Plot Loss Curve

    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Total Training Loss', linewidth=2)
    plt.title('MSCNN-LSTMNet Training Convergence', fontsize=14)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()


if __name__ == '__main__':
    train_mscnn_lstm()