from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import numpy as np
import torch
import pandas as pd
from Code.Test_12_1 import read_data
from sklearn.decomposition import PCA
import torch


# =====================================================================================================================
# Prototype 1: PCA Trend Extraction for Windows (Legacy / Reference)
# =====================================================================================================================
# def get_pca_trend(x_window):
#     """
#     Extracts trend features using PCA from a single data window.
#     """
#     # x_window: tensor, shape (window_size, num_features) e.g., (5, 12)
#     x_np = x_window.cpu().numpy()  # shape (5, 12)
#     trends = []
#     pca = PCA(n_components=1)
#     pca.fit(x_np)   # shape: (5, 12)
#     # Code for per-feature PCA (commented out in original)
#     # ...
#
#     pc1 = pca.components_[0]  # shape: (num_features,)
#     # PC1 represents the weight contribution of each dimension to the first principal component.
#     # It serves as the 'trend vector'.
#     trend = torch.tensor(pc1, dtype=torch.float32)  # shape: (12,)
#     return trend


# class TrendMeanDataset(Dataset):
#     """
#     Dataset class that generates Trend and Mean feature maps from time-series data.
#     """
#     def __init__(self, data, labels, window_size=5, stride=1):
#         self.window_size = window_size
#         self.stride = stride
#         self.data = torch.tensor(data, dtype=torch.float32)
#         self.labels = torch.tensor(labels.to_numpy(), dtype=torch.long)
#         # Generate all starting indices for sliding windows
#         self.indices = [i for i in range(0, len(self.labels) - window_size + 1, stride)]
#         self.x_time = torch.arange(window_size).float()
#
#     def __len__(self):
#         return len(self.indices)
#
#     def __getitem__(self, idx):
#         base_idx = self.indices[idx]
#         x_window = self.data[base_idx:base_idx + self.window_size]  # [win, D]
#         trends, means = [], []
#
#         # Calculate mean value for each feature dimension across the window
#         for i in range(x_window.shape[1]):  # Iterate over features
#             y = x_window[:, i]
#             y_mean = y.mean()
#             means.append(y_mean.item())
#
#         trends = get_pca_trend(x_window)   # Returns shape (12,)
#         trend_img = trends.clone().detach().view(3, 4)  # Reshape to image format (3, 4)
#         mean_img = torch.tensor(means).view(3, 4)       # Reshape to image format (3, 4)
#
#         # Stack to create a 2-channel image: [Trend_Channel, Mean_Channel]
#         x = torch.stack([trend_img, mean_img], dim=0)  # Shape: (2, 3, 4)
#         y = self.labels[base_idx + self.window_size]
#         return x


# =====================================================================================================================
# Prototype 2: Optimized PCA Extraction (Legacy / Reference)
# =====================================================================================================================
# def get_pca_trend(x_window):
#     x_np = x_window.view(x_window.size(0), -1).cpu().detach().numpy()
#     pca = PCA(n_components=1)
#     pca.fit(x_np)
#     pc1 = pca.components_[0]  # shape: (feature_dim,)
#     trend = torch.tensor(pc1, dtype=torch.float32)
#     return trend  # shape: (12,)
#
#
# class TrendMeanDataset(Dataset):
#     def __init__(self, data, labels=None, window_size=5, stride=3):
#         # Ensure data is FloatTensor
#         self.data = data.float() if isinstance(data, torch.Tensor) else torch.tensor(data, dtype=torch.float32)
#
#         # Label processing
#         if labels is not None:
#             self.labels = labels.long() if isinstance(labels, torch.Tensor) else torch.tensor(labels, dtype=torch.long)
#             assert self.data.size(0) == self.labels.size(0), "Data and Label length mismatch."
#         else:
#             self.labels = None
#
#         self.window_size = window_size
#         self.stride = stride
#
#         # Calculate valid start indices for sliding windows
#         # Ensure the window + prediction horizon fits within data
#         max_index = len(self.data) - window_size - (1 if self.labels is not None else 0)
#         if max_index < 0:
#             raise ValueError(f"Insufficient data for windowing. Need at least {window_size + 1}, got {len(self.data)}.")
#         self.indices = list(range(0, max_index + 1, stride))
#
#     def __len__(self):
#         return len(self.indices)
#
#     def __getitem__(self, idx):
#         base_idx = self.indices[idx]
#         x_window = self.data[base_idx: base_idx + self.window_size]  # [window_size, feature_dim]
#
#         # Compute Mean Image
#         if x_window.ndim == 4:  # Case: [Batch, Time, H, W] or similar
#             # Average across Batch and Channel/Time dimensions
#             mean_img = x_window.mean(dim=(0, 1)).view(3, 4)
#         elif x_window.ndim == 3:  # Case: [Time, H, W]
#             # Average across Time dimension
#             mean_img = x_window.mean(dim=0).view(3, 4)
#         else:
#             raise ValueError(f"Unsupported input tensor dimension: {x_window.shape}")
#
#         # Compute Trend Image (Assuming get_pca_trend returns a flat vector)
#         trend = get_pca_trend(x_window).view(-1, 3, 4)
#         trend_img = trend.mean(dim=0).view(3, 4)
#
#         # Stack channels
#         x = torch.stack([trend_img, mean_img], dim=0)  # Shape: [2, 3, 4]
#
#         if self.labels is not None:
#             y = self.labels[base_idx + self.window_size]
#             return x, y
#         else:
#             return x


# =====================================================================================================================
# Implementation 3: Current Production Code
# =====================================================================================================================

def get_batch_pca_trend(x_batch):
    """
    Computes the Principal Component Analysis (PCA) trend for a batch of feature maps.

    Args:
        x_batch (torch.Tensor): Input tensor of shape [B, C, H, W].

    Returns:
        torch.Tensor: Trend tensor of shape [C, H, W] representing the direction of maximum variance (PC1).
    """
    B, C, H, W = x_batch.shape
    device = x_batch.device

    # Flatten the batch to [B, Features] for PCA compatibility
    x_flattened = x_batch.view(B, -1).cpu().detach().numpy()

    # PCA requires at least 2 samples to calculate variance
    if x_flattened.shape[0] < 2:
        return torch.zeros(C, H, W, device=device)

    pca = PCA(n_components=1)
    pca.fit(x_flattened)

    # Extract the first principal component (PC1)
    pc1_vector = pca.components_[0]
    trend_vector_torch = torch.tensor(pc1_vector, dtype=torch.float32, device=device)

    # Reshape back to the original spatial dimensions
    return trend_vector_torch.view(C, H, W)


def get_patches_pca_trend_v1(patches_batch):
    """
    Calculates the trend vector (PC1) for a batch of image patches.

    Note:
        For performance optimization, calculating Standard Deviation (std)
        is often a faster alternative: `torch.std(patches_batch.view(N, C, -1), dim=2)`.
    """
    N, C, k, k_ = patches_batch.shape
    device = patches_batch.device

    # Flatten each window/patch for PCA
    patches_flat = patches_batch.view(N, -1).cpu().detach().numpy()

    # Check if sample size is sufficient for PCA
    if patches_flat.shape[0] < 2:
        return torch.zeros(N, C * k * k, device=device)  # Return zero vector if insufficient data

    pca = PCA(n_components=1)
    pca.fit(patches_flat)
    pc1 = pca.components_[0]  # First Principal Component

    # In this simplified version, we assign the global PC1 of the batch to all windows.
    # A more complex approach would project each window onto the PC components.
    trend_vector = torch.tensor(pc1, dtype=torch.float32, device=device)

    # Replicate the trend vector N times to match the batch size
    return trend_vector.repeat(N, 1)


class MLPFilterGenerator(nn.Module):
    """
    MLP-based Dynamic Filter Generator.

    This module generates convolution kernel weights dynamically based on the input features.
    """

    def __init__(self, in_features=2 * 3 * 4, out_channels=64, in_channels=2, kernel_size=3, MLP_hidden=4):
        super().__init__()
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.in_channels = in_channels
        # self.MLP_hidden = MLP_hidden

        # Multi-Layer Perceptron to map flattened features to filter weights
        self.mlp = nn.Sequential(
            nn.Linear(in_features, MLP_hidden),
            nn.ReLU(),
            # Output size = Total parameters needed for the conv layer weights
            nn.Linear(MLP_hidden, out_channels * self.in_channels * kernel_size * kernel_size)
        )

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): Input feature tensor, shape (B, 2, 3, 4).
        Returns:
            filters (torch.Tensor): Generated dynamic filters, shape (B, Out, In, K, K).
        """
        B = x.size(0)
        x_flat = x.view(B, -1)  # Flatten input features

        weights = self.mlp(x_flat)  # Generate weights via MLP

        # Reshape the flat weights into the format required for convolution:
        # [Batch, Out_Channels, In_Channels, Kernel_H, Kernel_W]
        filters = weights.view(B, self.out_channels, self.in_channels, self.kernel_size, self.kernel_size)
        # print('///', filters.shape)
        return filters


def get_Filter(x, in_features, out_channels, kernel_size):
    """
    Wrapper function to generate filters for a given input.

    WARNING: This function initializes a NEW MLPFilterGenerator every time it is called.
    The weights will be random and not trained.
    This is likely for demonstration or dimension testing only.
    """
    # x shape: [Batch, Channels, Height, Width]
    _, in_channels, _, _ = x.shape

    # Initialize the generator (New instance created on every call)
    mlp_filter_generator = MLPFilterGenerator(in_features=in_features,
                                              out_channels=out_channels,
                                              kernel_size=kernel_size,
                                              in_channels=in_channels)

    # Generate filters
    filters = mlp_filter_generator(x)  # Shape: [Batch, Out_Channels, In_Channels, K, K]

    # all_filters.append(filters.detach().cpu())
    # print("Filter Shape:", filters.shape)
    return filters


if __name__ == '__main__':
    # Configuration
    batch_size = 32

    # --- 1. Data Loading ---
    # Load dataset loaders (Training, Validation, Testing)
    # train_loader, val_loader, test_loader = read_data(batch_size)

    # --- 2. (Legacy) Manual Data Loading & Splitting Example ---
    # This block is commented out but shows how to manually prepare the dataset.
    # data = pd.read_csv('../data/100%_engine_dataset.csv')
    # X = data.drop('y_label', axis=1)
    # y = data['y_label']
    # scaler = StandardScaler()
    # X_scaled = scaler.fit_transform(X)
    #
    # # Select specific sensors/features
    # selected_parameters = np.array([4, 5, 6, 7, 8, 9, 10, 14, 16, 20, 21, 23])
    # handle_data = X_scaled[:, selected_parameters]
    #
    # # Stratified Split
    # X_train_1, X_test_1, y_train_1, y_test_1 = train_test_split(handle_data, y, test_size=0.3, stratify=y, random_state=42)
    # X_train_1, X_val_1, y_train_1, y_val_1 = train_test_split(X_train_1, y_train_1, test_size=0.25, stratify=y_train_1, random_state=42)
    #
    # # Dataset Initialization
    # dataset = TrendMeanDataset(X_train_1, y_train_1, window_size=5, stride=3)
    # train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

    # --- 3. Dynamic Filter Testing ---
    train_loader, val_loader, test_loader = read_data(batch_size)
    x_batch, y_train = next(iter(train_loader))

    # Test the filter generation wrapper
    # Note: inputs are flattened internally from (B, 2, 3, 4) -> (B, 24)
    # Output filters will be [B, 256, 2, 3, 3]
    get_Filter(x_batch, in_features=2 * 3 * 4, out_channels=256, kernel_size=3)

    # --- 4. (Legacy) Detailed Testing Loop ---
    # This block demonstrates how to iterate and visualize filters.
    """
    # Initialize MLP Filter Generator
    mlp_filter_generator = MLPFilterGenerator(in_features=2 * 3 * 4, out_channels=64, kernel_size=3)

    all_filters = []
    # Test on a single batch
    for x_batch, y_batch in train_loader:
        print("Input Shape:", x_batch.shape)  # e.g., [32, 2, 3, 4]

        # Dynamic Filter Generation:
        # Each sample and channel (Trend, Mean) generates a unique filter
        # guided by the input statistics.
        filters = mlp_filter_generator(x_batch)  # Output: [32, 64, 2, 3, 3]
        all_filters.append(filters.detach().cpu())
        print("Generated Filter Shape:", filters.shape)
        break

    # --- Visualization ---
    import matplotlib.pyplot as plt
    sample_idx = 0  # Select first sample in the batch
    sample_filters = all_filters[sample_idx]  # Shape: (64, 2, 3, 3)

    channel_idx = 0  # Select filters corresponding to the 1st input channel
    num_show = 6     # Number of filters to visualize

    fig, axes = plt.subplots(1, num_show, figsize=(3 * num_show, 3))

    for i in range(num_show):
        # Extract kernel for (Filter i, Channel 0)
        kernel = sample_filters[i, channel_idx].detach().cpu().numpy()  # (3, 3)
        axes[i].imshow(kernel, cmap='viridis', interpolation='nearest') # Fixed kernel[0] to kernel
        axes[i].set_title(f'Filter {i} Ch {channel_idx}')
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()
    """