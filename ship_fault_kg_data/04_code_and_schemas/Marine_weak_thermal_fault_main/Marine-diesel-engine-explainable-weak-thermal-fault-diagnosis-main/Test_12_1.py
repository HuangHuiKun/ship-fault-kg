from torch.utils.data import Dataset, DataLoader, Sampler, BatchSampler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from torchvision import transforms
from PIL import Image
from Code.config import *  # Assuming config contains necessary paths or constants


# =====================================================================================================================
class ParamDataset(Dataset):
    """
    Custom Dataset for Engine Parameters.

    Processing Steps:
    1. Converts 1D parameter vectors into 2D feature maps (Images).
    2. Applies Instance-wise Min-Max Normalization.
    3. Performs Data Augmentation (Noise Injection, Pixel/Patch Masking).
    """

    def __init__(self, data1, data2, labels):
        """
        Args:
            data1 (np.array): Primary sensor data.
            data2 (np.array): Secondary or Residual sensor data.
            labels (list/np.array): Classification labels.
        """
        self.data1 = torch.tensor(data1, dtype=torch.float32)
        self.data2 = torch.tensor(data2, dtype=torch.float32)
        self.labels = torch.tensor(np.array(labels), dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # --- 1. Load Raw Data ---
        x1 = self.data1[idx]
        x2 = self.data2[idx]

        # --- 2. Instance-wise Min-Max Normalization ---
        # Normalize each sample independently to [0, 1] range to capture the trend shape
        # regardless of the absolute magnitude.
        x1_norm = (x1 - x1.min()) / (x1.max() - x1.min() + 1e-8)  # Added epsilon for stability
        x2_norm = (x2 - x2.min()) / (x2.max() - x2.min() + 1e-8)

        # Reshape 1D vector (length 12) to 2D Feature Map (3x4)
        x1_img = x1_norm.view(3, 4)
        x2_img = x2_norm.view(3, 4)

        # --- 3. Data Augmentation: Noise Injection ---
        noise_std = 0.5
        # Add Gaussian noise to x1_img
        noise = torch.randn_like(x1_img) * noise_std
        x1_noisy = x1_img + noise

        # (Optional) Add noise to x2_img
        # noise2 = torch.randn_like(x2_img) * noise_std
        # x2_noisy = x2_img + noise2

        # --- 4. Data Augmentation: Random Masking / Erasing ---
        # Strategy A: Single Pixel Masking (Simulating single sensor failure)
        # Masking the pixel at row 2, col 3 (Index starts from 0)
        y, x = 2, 3
        image_masked_single = x1_img.clone()  # Clone to avoid modifying the original tensor
        image_masked_single[y, x] = 0

        # Strategy B: Patch Masking (Simulating regional data loss)
        # Masking a 2x2 region starting from (1, 1)
        y_start, x_start = 1, 1
        height, width = 2, 2  # Fixed: changed comment from 3,3 to 2,2 to match logic if intended
        image_masked_patch = x1_img.clone()
        image_masked_patch[y_start:y_start + height, x_start:x_start + width] = 0

        # --- Visualization (Debug Only) ---
        # plt.figure(figsize=(10, 5))
        # plt.subplot(1, 2, 1)
        # plt.imshow(x1_img, cmap="gray")
        # plt.title("Original Normalized Data")
        # plt.axis('off')
        #
        # plt.subplot(1, 2, 2)
        # plt.imshow(x1_noisy, cmap="gray")
        # plt.title("Noisy/Masked Data")
        # plt.axis('off')
        # plt.show()

        # --- 5. Construct Final Input Tensor ---
        # Current: Return single channel [1, 3, 4]
        x = torch.stack([x1_img], dim=0)

        # Alternative: Return dual channel [2, 3, 4]
        # x = torch.stack([x1_img, x2_img], dim=0)

        # Alternative: Return masked version
        # x = torch.stack([image_masked_patch], dim=0)

        return x, self.labels[idx]


# =====================================================================================================================
def split_by_time_per_class(X, y, train_ratio=0.7, val_ratio=0.15):
    """
    Splits the dataset chronologically within each class.

    Motivation:
    For time-series or sequential data, random splitting causes data leakage
    (training on future data and predicting past data). This function ensures
    strict temporal separation.
    """
    classes = np.unique(y)
    X_train, y_train = [], []
    X_val, y_val = [], []
    X_test, y_test = [], []

    for cls in classes:
        idx = np.where(y == cls)[0]  # Get indices for the current class
        idx_sorted = np.sort(idx)  # Ensure chronological order

        n_total = len(idx_sorted)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)

        # Slice indices chronologically
        train_idx = idx_sorted[:n_train]
        val_idx = idx_sorted[n_train:n_train + n_val]
        test_idx = idx_sorted[n_train + n_val:]

        X_train.append(X[train_idx])
        y_train.append(y[train_idx])

        X_val.append(X[val_idx])
        y_val.append(y[val_idx])

        X_test.append(X[test_idx])
        y_test.append(y[test_idx])

    # Concatenate results from all classes
    X_train = np.concatenate(X_train)
    y_train = np.concatenate(y_train)
    X_val = np.concatenate(X_val)
    y_val = np.concatenate(y_val)
    X_test = np.concatenate(X_test)
    y_test = np.concatenate(y_test)

    return X_train, X_val, X_test, y_train, y_val, y_test


# =====================================================================================================================
class StratifiedBatchSampler(Sampler):
    """
    A Batch Sampler that ensures every batch is class-balanced.

    Mechanism:
    It iterates through all classes and picks a fixed number of samples
    (`batch_size // num_classes`) from each class to form a batch.
    This is useful for training with highly imbalanced datasets.
    """

    def __init__(self, labels, batch_size):
        self.labels = np.array(labels)
        self.batch_size = batch_size
        self.unique_classes = np.unique(labels)
        self.class_indices = {cls: np.where(self.labels == cls)[0] for cls in self.unique_classes}

        # Calculate samples per class per batch
        self.num_classes = len(self.unique_classes)
        self.samples_per_class = batch_size // self.num_classes

    def __iter__(self):
        # Create iterators for each class
        class_iters = {cls: iter(indices) for cls, indices in self.class_indices.items()}
        while True:
            batch = []
            for cls in self.unique_classes:
                cls_samples = []
                try:
                    for _ in range(self.samples_per_class):
                        cls_samples.append(next(class_iters[cls]))
                except StopIteration:
                    # Stop if any class runs out of data (simplest approach)
                    return
                batch.extend(cls_samples)

            # Shuffle the constructed balanced batch
            np.random.shuffle(batch)
            yield batch

    def __len__(self):
        # Estimate the number of batches based on the limiting class
        min_class_len = min(len(indices) for indices in self.class_indices.values())
        return (min_class_len // self.samples_per_class)


# =====================================================================================================================
def read_data(batch_size=16):
    """
    Data Pipeline: Loading -> Feature Selection -> Residual Construction -> Splitting -> Scaling.
    """
    # 1. Load Data
    data = pd.read_csv('../Engine_dataset.csv')
    X = data.drop('y_label', axis=1)
    y = data['y_label']

    # 2. Feature Selection
    # Select 12 specific sensor parameters based on domain knowledge/feature importance
    selected_parameters = np.array([4, 5, 6, 7, 8, 9, 10, 14, 16, 20, 21, 23])
    handle_data = X.values[:, selected_parameters]

    # 3. Data Subsetting (Sample Selection)
    # E.g., Select 30 samples (index 100 to 200?) per class
    # Note: Logic below selects indices [start_idx:end_idx] relative to the class, not absolute count 100-200.
    num_classes = len(np.unique(y))
    start_idx, end_idx = 100, 200
    X_list = []
    y_list = []

    for cls in range(num_classes):
        cls_indices = np.where(y == cls)[0]
        if len(cls_indices) < end_idx:
            print(f"Warning: Class {cls} has insufficient samples ({len(cls_indices)} < {end_idx}). Skipping.")
            continue

        selected_indices = cls_indices[start_idx:end_idx]
        X_list.append(handle_data[selected_indices])
        y_list.append(y.iloc[selected_indices])

    handle_data = np.vstack(X_list)
    y = pd.concat(y_list, ignore_index=True)

    # 4. Residual Data Construction
    # Hypothesis: The difference between specific classes and a baseline (Class 10) contains fault features.
    mask_10 = (y == 10)
    data_10_all = handle_data[mask_10]
    y_10_all = y[mask_10]

    # Baseline vector (last sample of class 10) - Verify if this single sample is representative enough
    x10 = handle_data[mask_10][-1]

    mask_0to9 = (y >= 0) & (y <= 9)
    data_0to9 = handle_data[mask_0to9]
    labels_0to9 = y[mask_0to9]

    # Calculate residuals
    residuals = data_0to9 - x10

    # Merge baseline data and residual data
    Residual_data = np.vstack([data_10_all, residuals])
    new_y = np.hstack([y_10_all, labels_0to9])

    # =================================================================================================================
    # Strategy 1: Random Stratified Split (Active)
    # Suitable for i.i.d data where time dependency is not critical or already handled.

    # Split primary data
    X_train_1, X_test_1, y_train_1, y_test_1 = train_test_split(handle_data, y, test_size=0.15, stratify=y,
                                                                random_state=42)
    X_train_1, X_val_1, y_train_1, y_val_1 = train_test_split(X_train_1, y_train_1, test_size=0.15, stratify=y_train_1,
                                                              random_state=42)

    # Split residual data (using same random state to arguably keep alignment, but separate calls may misalign if not careful)
    # Ideally, split indices first, then apply to both datasets to ensure X_train_1[i] corresponds to X_train_2[i].
    # HERE: Assuming statistical distribution is enough, but strictly speaking, correspondence might be lost if not aligned by index.
    X_train_2, X_test_2, y_train_2, y_test_2 = train_test_split(Residual_data, new_y, test_size=0.15, stratify=new_y,
                                                                random_state=42)
    X_train_2, X_val_2, y_train_2, y_val_2 = train_test_split(X_train_2, y_train_2, test_size=0.15, stratify=y_train_2,
                                                              random_state=42)

    # 5. Global Standardization
    scaler = StandardScaler()
    X_train_1 = scaler.fit_transform(X_train_1)
    X_val_1 = scaler.transform(X_val_1)
    X_test_1 = scaler.transform(X_test_1)

    X_train_2 = scaler.fit_transform(X_train_2)
    X_val_2 = scaler.transform(X_val_2)
    X_test_2 = scaler.transform(X_test_2)

    # 6. Create Datasets and Loaders
    # Note: .to_numpy() needed if y is Series, already numpy if from split_by_time
    train_set = ParamDataset(X_train_1, X_train_2, y_train_1.to_numpy())
    val_set = ParamDataset(X_val_1, X_val_2, y_val_1.to_numpy())
    test_set = ParamDataset(X_test_1, X_test_2, y_test_1.to_numpy())

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

    # =================================================================================================================
    # Strategy 2: Time-Series Split (Commented Out)
    # Use this if preventing future-leakage is priority.
    """
    X_train_1, X_val_1, X_test_1, y_train_1, y_val_1, y_test_1 = split_by_time_per_class(handle_data, y)
    X_train_2, X_val_2, X_test_2, y_train_2, y_val_2, y_test_2 = split_by_time_per_class(Residual_data, new_y)

    train_set = ParamDataset(X_train_1, X_train_2, y_train_1)
    val_set = ParamDataset(X_val_1, X_val_2, y_val_1)
    test_set = ParamDataset(X_test_1, X_test_2, y_test_1)

    # Shuffle must be True for training to prevent gradient oscillation
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)
    """

    return train_loader, val_loader, test_loader


if __name__ == '__main__':
    from Code.Test_12_1_1 import MLPFilterGenerator

    train_loader, val_loader, test_loader = read_data()

    # Initialize Generator
    # Input features: 1 channel * 3 height * 4 width = 12 flattened features
    mlp_filter_generator = MLPFilterGenerator(in_features=1 * 3 * 4, out_channels=64, kernel_size=3)

    all_filters = []

    # Test with one batch
    for x_batch, y_batch in train_loader:
        print(f"Input Shape: {x_batch.shape}")  # Expected: [Batch, 1, 3, 4]

        # Generate Dynamic Filters
        # Shape interpretation: [Batch, Out_Channels, In_Channels, kH, kW]
        # Here: [32, 64, 2, 3, 3] implies the generator is creating filters for a 2-channel input?
        # CAUTION: If x_batch is 1 channel, but filters are 2 channel (as per your print comment),
        # ensure MLPFilterGenerator configuration matches the subsequent convolution layer.
        filters = mlp_filter_generator(x_batch)

        all_filters.append(filters.detach().cpu())
        print(f"Generated Filter Shape: {filters.shape}")
        break