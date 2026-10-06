import torch
import os
from torch import nn
from torch.utils.data import DataLoader
import numpy as np
from Code.Test_12 import DPFD_ACAM_ISimAM_TwoChannelFusion, DynamicConv2D_v4
from Code.Test_12_1 import read_data
from Code.config import *
import torch.nn.functional as F
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import seaborn as sns
from sklearn.metrics import confusion_matrix
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from itertools import cycle
from matplotlib.patches import Rectangle

# Create directory if it does not exist
os.makedirs(folder_path, exist_ok=True)


# ======================================================================================================================
# ---------- 1. Noise Injection Functions (Robustness Testing) ----------
# These functions simulate different types of sensor noise to test model stability.
# ======================================================================================================================

def add_gaussian(x, sigma):
    """Adds Gaussian noise to the input tensor."""
    return x + sigma * torch.randn_like(x)


def add_salt_pepper(x, p=0.01):
    """
    Adds Salt-and-Pepper noise.
    Pixels are randomly set to min or max values based on probability p.
    """
    mask = torch.rand_like(x)
    x_sp = x.clone()
    # Salt (max value) and Pepper (min value)
    x_sp[mask < p / 2] = x.min()
    x_sp[(mask >= p / 2) & (mask < p)] = x.max()
    return x_sp


def add_multiplicative(x, sigma=0.1):
    """Adds Multiplicative (Speckle) noise: x = x * (1 + noise)."""
    return x * (1 + sigma * torch.randn_like(x))


# ======================================================================================================================
# ---------- 2. Visualization Utilities (ROC Curve) ----------
# ======================================================================================================================

def plot_multiclass_roc_curve(y_true, y_proba, class_labels, temp_num, x_width, y_height):
    """
    Plots the Receiver Operating Characteristic (ROC) curve for multi-class classification using One-vs-Rest strategy.
    Includes Micro-average and Macro-average curves.

    Args:
        y_true (array): True labels (e.g., [0, 1, 2]).
        y_proba (array): Predicted probabilities of shape (n_samples, n_classes).
        class_labels (list): List of class names.
        temp_num (int): Identifier for saving the file (e.g., experiment number).
        x_width (float): Width of the zoomed-in inset on the X-axis.
        y_height (float): Starting height of the zoomed-in inset on the Y-axis.
    """
    n_classes = len(class_labels)

    #
    # 1. Binarize labels for One-vs-Rest calculation
    y_true_bin = label_binarize(y_true, classes=range(n_classes))

    # Dictionaries to store metrics
    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    # --- Compute ROC for each class ---
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_true_bin[:, i], y_proba[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # --- Compute Micro-average ROC ---
    fpr["micro"], tpr["micro"], _ = roc_curve(y_true_bin.ravel(), y_proba.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    # --- Compute Macro-average ROC ---
    # Aggregate all false positive rates
    all_fpr = np.unique(np.concatenate([fpr[i] for i in range(n_classes)]))

    # Interpolate all ROC curves at these points
    mean_tpr = np.zeros_like(all_fpr)
    for i in range(n_classes):
        mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])

    mean_tpr /= n_classes
    fpr["macro"] = all_fpr
    tpr["macro"] = mean_tpr
    roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])

    # --- Plotting ---
    plt.figure(figsize=(12, 10))

    # Plot Micro & Macro Averages
    plt.plot(fpr["micro"], tpr["micro"],
             label=f'Micro-average (AUC = {roc_auc["micro"]:.2f})',
             color='deeppink', linewidth=2)

    plt.plot(fpr["macro"], tpr["macro"],
             label=f'ROC (AUC = {roc_auc["macro"]:.2f})',
             color='navy', linewidth=2)

    # Plot Per-Class Curves
    colors_cycle = cycle([
        'aqua', 'darkorange', 'cornflowerblue', 'green', 'red',
        'purple', 'gold', 'pink', 'brown', 'lime', 'magenta'
    ])

    for i, c in zip(range(n_classes), colors_cycle):
        plt.plot(fpr[i], tpr[i], color=c, lw=2,
                 label=f'{class_labels[i]} (AUC = {roc_auc[i]:.2f})')

    # Diagonal random guess line
    plt.plot([0, 1], [0, 1], 'k--', lw=2)

    # Chart formatting
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['axes.unicode_minus'] = False
    plt.xlim([-0.02, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=30)
    plt.ylabel('True Positive Rate', fontsize=30)
    plt.legend(loc="lower right", fontsize=15)
    plt.tick_params(axis='x', labelsize=30)
    plt.tick_params(axis='y', labelsize=30)
    plt.tick_params(axis='both', which='both', direction='in')

    # --- Add Zoomed-In Inset ---
    ax = plt.gca()
    inset_pos = [0.69, 0.55, 3, 3]  # [x0, y0, width, height]
    x0, y0, w, h = inset_pos

    # Define area to zoom in (Top-Left corner usually)
    x1, x2 = 0, x_width
    y1, y2 = y_height, 1.0

    axins = inset_axes(ax, width=w, height=h, loc='lower left', bbox_to_anchor=(x0, y0, w, h),
                       bbox_transform=ax.transAxes)

    # Draw rectangle on main plot to indicate zoomed area
    pad_x = (x2 - x1) * 0.1
    pad_y = (y2 - y1) * 0.1
    rect = Rectangle((x1 - pad_x, y1 - pad_y),
                     (x2 - x1) + 2 * pad_x,
                     (y2 - y1) + 2 * pad_y,
                     linewidth=1.5, edgecolor='red', facecolor='lightgray', alpha=0.3, linestyle='--')
    ax.add_patch(rect)

    # Setup inset plot
    axins.patch.set_alpha(0.0)  # Transparent background
    padding_x = (x2 - x1) * 0.05
    padding_y = (y2 - y1) * 0.05
    axins.set_xlim(x1 - padding_x, x2 + padding_x)
    axins.set_ylim(y1 - padding_y, y2 + padding_y)

    # Set ticks for inset
    xticks = np.round(np.linspace(x1, x2, 4), 2)
    yticks = np.round(np.linspace(y1, y2, 4), 2)
    axins.set_xticks(xticks)
    axins.set_yticks(yticks)
    axins.tick_params(labelsize=15)

    # Re-plot curves in inset
    axins.plot(fpr["micro"], tpr["micro"], color='deeppink', linewidth=2)
    axins.plot(fpr["macro"], tpr["macro"], color='navy', linewidth=2)
    for j, c in zip(range(n_classes), colors_cycle):
        axins.plot(fpr[j], tpr[j], color=c, lw=2)

    plt.tight_layout()
    plt.savefig(folder_path + "/multiclass_roc_" + str(temp_num) + ".png", dpi=300)
    plt.show()


# ======================================================================================================================
# ---------- 3. Occlusion Sensitivity Analysis ----------
# ======================================================================================================================

def occlusion_sensitivity_test(model, test_loader, patch_size=(1, 1), device='cpu'):
    """
    Performs occlusion sensitivity testing on the dataset.
    Randomly masks a patch in the input and measures accuracy drop.

    Args:
        model: Trained PyTorch model.
        test_loader: DataLoader for the test set.
        patch_size: Tuple (h, w) of the occlusion patch size.
        device: 'cpu' or 'cuda'.

    Returns:
        tuple: (original_acc, occluded_acc)
    """

    total_samples = 0
    correct_original = 0
    correct_occluded = 0

    for X, y in test_loader:
        X, y = X.to(device), y.to(device)
        batch_size, C, H, W = X.shape
        total_samples += y.size(0)

        # -------------------
        # 1. Evaluate Original Accuracy
        with torch.no_grad():
            outputs = model(X)
            preds = outputs.argmax(1)
            correct_original += (preds == y).sum().item()

        # -------------------
        # 2. Evaluate Occluded Accuracy
        X_occluded = X.clone()
        # Randomly occlude a patch for each image in the batch
        for i in range(batch_size):
            y_start = np.random.randint(0, H - patch_size[0] + 1)
            x_start = np.random.randint(0, W - patch_size[1] + 1)
            X_occluded[i, :, y_start:y_start + patch_size[0], x_start:x_start + patch_size[1]] = 0

        with torch.no_grad():
            outputs_occ = model(X_occluded)
            preds_occ = outputs_occ.argmax(dim=1)
            correct_occluded += (preds_occ == y).sum().item()

    original_acc = correct_original / total_samples
    occluded_acc = correct_occluded / total_samples

    # print(f"Original Acc: {original_acc * 100:.2f}%")
    # print(f"Occluded Acc: {occluded_acc * 100:.2f}%")
    # print(f"Accuracy Drop: {(original_acc - occluded_acc) * 100:.2f}%")

    return original_acc, occluded_acc


# ======================================================================================================================
# ---------- 4. Specialized Test Functions ----------
# ======================================================================================================================

def test_with_noise(model, test_loader, device, noise_std=0.5):
    """Evaluates model performance under noise injection."""
    model.eval()
    correct = 0
    total = 0
    all_preds, all_labels, all_features = [], [], []

    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)

            # Apply Noise (Select one strategy: Gaussian, Salt & Pepper, or Multiplicative)
            # noisy_images = add_salt_pepper(images, p=0.01)
            noisy_images = add_gaussian(images, noise_std)

            outputs = model(noisy_images)
            _, preds = torch.max(outputs, 1)

            correct += (preds == labels).sum().item()
            total += labels.size(0)

            all_preds.append(preds.cpu())
            all_labels.append(labels.cpu())
            all_features.append(outputs.cpu())

    acc = correct / total
    print(f"Test Acc (Noisy): {acc * 100:.2f}%")
    return acc, torch.cat(all_preds), torch.cat(all_labels), torch.cat(all_features)


def test_with_mask(model, test_loader, device, mask_type="pixel", y=2, x=3,
                   y_start=1, x_start=1, height=2, width=2):
    """
    Evaluates model performance with fixed masking (Pixel or Patch).

    Args:
        mask_type: "pixel" (single point) or "patch" (region).
    """
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)

            masked_images = images.clone()

            if mask_type == "pixel":
                # Mask a specific pixel (simulate sensor failure)
                masked_images[:, :, y, x] = 0

            elif mask_type == "patch":
                # Mask a specific region (simulate local data loss)
                masked_images[:, :, y_start:y_start + height, x_start:x_start + width] = 0

            outputs = model(masked_images)
            _, preds = torch.max(outputs, 1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    acc = correct / total
    # print(f"Test Acc ({mask_type} mask): {acc* 100:.2f}%")
    return acc


# ======================================================================================================================
# ---------- Main Execution Block ----------
# ======================================================================================================================

# 1. Load Data and Model
train_loader, val_loader, test_loader = read_data(Batch_size)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DPFD_ACAM_ISimAM_TwoChannelFusion(In_channels, Conv_channels, Cbam_reduction).to(device)

# 2. Load Checkpoint
checkpoint = torch.load("../model/best_model_" + str(Model_id) + ".pth", map_location=device)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# 3. Robustness Experiments
# A. Random Occlusion Sensitivity (Baseline vs Occluded)
original_A, occluded_A = occlusion_sensitivity_test(model, test_loader, patch_size=(1, 1), device=device)

# B. Noise Robustness Test (Gaussian Noise)
# Parameters for visualization filtering
temp_num = 7
x_width = 0.05
y_height = 0.90
acc, preds, labels, feats = test_with_noise(model, test_loader, device, noise_std=0.07)

# C. Fixed Pixel Masking (e.g., masking pixel at y=2, x=3)
test_with_mask(model, test_loader, device, mask_type="pixel", y=2, x=3)

# D. Fixed Patch Masking (e.g., region starting at y=0, x=3)
test_with_mask(model, test_loader, device, mask_type="patch", y_start=0, x_start=3, height=1, width=1)

# ======================================================================================================================
# ---------- Visualization ----------
# ======================================================================================================================

# 1. t-SNE Visualization
n_classes = 11
plt.figure(figsize=(16, 9))
tsne = TSNE(n_components=2, random_state=42, perplexity=6, learning_rate=100, n_iter=1000)
features_2d = tsne.fit_transform(feats)

# Define Styles
custom_markers = {'d1': 'o', 'd2': 's', 'd3': 'D', 'd4': '^', 'd5': 'v',
                  'd6': '<', 'd7': '>', 'd8': 'P', 'd9': '*', 'd10': 'p', 'd11': 'h'}
custom_palette = {'d1': 'red', 'd2': 'blue', 'd3': 'green', 'd4': 'orange', 'd5': 'purple',
                  'd6': 'cyan', 'd7': 'orchid', 'd8': 'darkviolet', 'd9': 'brown',
                  'd10': 'pink', 'd11': 'gray'}
label_mapping = {i: f'd{i + 1}' for i in range(11)}

# Prepare Data Frame
import pandas as pd

df = pd.DataFrame({
    "x": features_2d[:, 0],
    "y": features_2d[:, 1],
    "label": labels
})
df["label"] = df["label"].map(label_mapping)

# Plot
ax = sns.scatterplot(
    data=df,
    x="x", y="y",
    hue="label", style="label",
    palette=custom_palette, markers=custom_markers,
    s=500  # Marker size
)

# Style Spines
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_color('black')
    spine.set_linewidth(1.5)

plt.tick_params(axis='x', labelsize=30)
plt.tick_params(axis='y', labelsize=30)
plt.xlabel('Thermal feature Dim 1', fontsize=30)
plt.ylabel('Thermal feature Dim 2', fontsize=30)
plt.tick_params(axis='both', which='both', direction='in')

# Legend
legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), fontsize=30, ncol=6)
for handle in legend.legendHandles:
    handle.set_sizes([300])

plt.grid(False)
plt.rcParams['font.family'] = 'Times New Roman'
plt.tight_layout()
plt.savefig(folder_path + "/tsne_" + str(temp_num) + ".png")
plt.show()

# 2. Confusion Matrix Visualization
plt.figure(figsize=(16, 9))
cm_tri = confusion_matrix(labels, preds)
ax = sns.heatmap(cm_tri, annot=True, fmt="d", cmap="Blues",
                 xticklabels=range(1, 12), yticklabels=range(1, 12),
                 annot_kws={"size": 30},
                 cbar_kws={"shrink": 0.8})

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=30)

for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_color('black')
    spine.set_linewidth(1.5)

plt.xlabel("Predicted Condition", fontsize=30)
plt.ylabel("Actual Condition", fontsize=30)
plt.xticks(fontsize=30)
plt.yticks(fontsize=30)
plt.rcParams['font.family'] = 'Times New Roman'
plt.tight_layout()
plt.savefig(folder_path + "/confusion_matrix_" + str(temp_num) + ".png")
plt.show()

# 3. ROC Curve Visualization
# Calculate softmax probabilities
y_proba = F.softmax(feats, dim=1)
# Define class names
class_names = [f'd{i + 1}' for i in range(11)]

# Plot
plot_multiclass_roc_curve(y_true=labels, y_proba=y_proba, class_labels=class_names,
                          temp_num=temp_num, x_width=x_width, y_height=y_height)