import os
from sklearn.metrics import precision_recall_curve, average_precision_score, classification_report
import shap
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
import torch
from sklearn.manifold import TSNE
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, \
    precision_recall_curve
import seaborn as sns
import torch.nn.functional as F
from Code.Test_12 import DPFD_ACAM_ISimAM_TwoChannelFusion
from Code.Test_12_1 import read_data
from Code.Test_12_2_2 import FusionCAM, normalize_cam, GradCAMpp, GradCAM_1
from Code.config import *
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib import cm, colors
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset
from matplotlib.patches import Rectangle
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from itertools import cycle

# Create directory if it does not exist
os.makedirs(folder_path, exist_ok=True)


# ======================================================================================================================
# ---------- SHAP Explainer Visualization ---------- #
def explain_with_shap(model, test_loader, device):
    """
    Uses SHAP (SHapley Additive exPlanations) to explain model predictions.
    Generates:
    1. Summary Plot: Global feature importance.
    2. Waterfall Plot: Local explanation for a single sample.
    3. Mean SHAP Bar Chart: Class-wise feature contribution.
    """
    import numpy as np

    # 1. Prepare Data
    # Get a small batch from test loader.
    # [0] is the input data (batch_size, 2, 3, 4), [1] is the label.
    batch = next(iter(test_loader))[0][:16].cpu().numpy()

    # Flatten data for SHAP KernelExplainer (Tabular format expected)
    # Shape: (batch_size, features) -> (16, 24) where 24 = 2*3*4
    batch_flat = batch.reshape(batch.shape[0], -1)

    # 2. Define Prediction Wrapper
    # SHAP expects a function that takes a numpy array and returns probabilities
    def model_predict(x_numpy):
        x_tensor = torch.tensor(x_numpy, dtype=torch.float32).to(device)
        # Reshape back to model input format: (Batch, Channels, Height, Width)
        x_tensor = x_tensor.view(-1, In_channels, 3, 4)
        with torch.no_grad():
            logits = model(x_tensor)
            probs = torch.nn.functional.softmax(logits, dim=1)
        return probs.cpu().numpy()

    # 3. Initialize Explainer
    # Use 10 random samples from the batch as the background dataset (baseline)
    background = batch_flat[np.random.choice(batch_flat.shape[0], 10, replace=False)]
    explainer = shap.KernelExplainer(model_predict, background)

    # Calculate SHAP values for the batch (nsamples controls the number of evaluations)
    # Returns a list of arrays, one per class
    shap_values_all = explainer.shap_values(batch_flat, nsamples=100)

    # 4. Configuration for Plotting
    class_idx = 0  # Target class index (e.g., Normal Condition)
    sample_idx = 0  # Index of the specific sample to visualize

    # Get SHAP values for the specific class and sample
    shap_values = shap_values_all[class_idx][sample_idx]

    # Get Base Value (Expected Value) for the class
    base_value = explainer.expected_value[class_idx]

    # Get original feature values for the sample
    feature_values = batch_flat[sample_idx]

    # Create Feature Names (P0 to P23)
    feature_names = [f'P{i}' for i in range(feature_values.shape[0])]

    # Calculate SHAP values for the first 20 samples for summary plot
    shap_values_1 = explainer.shap_values(batch_flat[:20], nsamples=100)

    # ==================================================================================================================
    # 5. Plot: Summary Plot (Global Importance)
    shap.summary_plot(shap_values_1[class_idx], features=batch_flat[:20],
                      feature_names=feature_names, show=False)
    plt.savefig(folder_path + "/features_importance.png", dpi=300)

    # ==================================================================================================================
    # 6. Plot: Waterfall Plot (Local Explanation)
    plt.figure(figsize=(16, 9))
    explanation = shap.Explanation(
        values=shap_values,
        base_values=base_value,
        data=feature_values,
        feature_names=feature_names
    )
    shap.waterfall_plot(explanation, show=False)
    plt.title("Waterfall Plot", fontsize=20)
    plt.xlabel("SHAP value", fontsize=30)
    plt.ylabel("Thermal parameter value", fontsize=30)
    plt.xticks(fontsize=30)
    plt.yticks(fontsize=30)
    plt.rcParams["font.family"] = "Times New Roman"
    plt.plot()
    plt.savefig(folder_path + "/Waterfall.png", dpi=300)
    plt.show()

    # ==================================================================================================================
    # 7. Plot: Mean SHAP Values (Stacked Bar Chart)
    # Calculate mean absolute SHAP value for each class
    class_mean_shap = []
    for c_idx in range(len(shap_values_1)):
        # Average across samples for the current class
        mean_shap = np.abs(shap_values_1[c_idx]).mean(axis=0)  # Shape: (n_features,)
        class_mean_shap.append(mean_shap)

    mean_shap_values = np.vstack(class_mean_shap)  # Shape: [n_classes, n_features]

    # Setup Colors
    n_classes = mean_shap_values.shape[0]
    colors_list = plt.cm.tab10.colors
    if n_classes > len(colors_list):
        import matplotlib
        cmap = matplotlib.cm.get_cmap('tab20')
        colors_list = [cmap(i) for i in range(n_classes)]

    # Drawing
    fig, ax = plt.subplots(figsize=(16, 14))
    y_pos = np.arange(len(feature_names))
    left = np.zeros(len(feature_names))  # Accumulator for stacking bars

    for i in range(n_classes):
        ax.barh(
            y_pos, mean_shap_values[i, :], left=left,
            color=colors_list[i % len(colors_list)], edgecolor='black', label=f'Class {i}'
        )
        left += mean_shap_values[i, :]  # Stack next bar

    ax.set_yticks(y_pos)
    ax.set_yticklabels(feature_names, fontsize=30)
    ax.set_xlabel('Mean SHAP value', fontsize=30)
    ax.set_ylabel('Thermal parameters', fontsize=30)
    ax.tick_params(axis='y', length=0)
    ax.tick_params(axis='x', direction='in', length=5, width=2, labelsize=30)
    ax.legend(title='Classes', bbox_to_anchor=(0.85, 1), loc='upper left', fontsize=30)
    plt.rcParams["font.family"] = "Times New Roman"
    plt.tight_layout()
    plt.savefig(folder_path + "//Mean_SHAP.png", dpi=300)
    plt.show()


# ======================================================================================================================
# ---------- ROC Curve Visualization ---------- #
def plot_multiclass_roc_curve(y_true, y_proba, class_labels):
    """
    Plots ROC curves for multi-class classification using One-vs-Rest (OvR) strategy.
    Includes Micro-average, Macro-average, and per-class curves with a zoomed-in inset.

    Args:
        y_true (array): True labels (e.g., [0, 1, 2]).
        y_proba (array): Predicted probabilities, shape (n_samples, n_classes).
        class_labels (list): List of class names.
    """
    n_classes = len(class_labels)

    # 1. Binarize labels for One-vs-Rest calculation
    y_true_bin = label_binarize(y_true, classes=range(n_classes))

    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    # 2. Compute ROC for each class
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_true_bin[:, i], y_proba[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # 3. Compute Micro-average ROC (Flattened arrays)
    fpr["micro"], tpr["micro"], _ = roc_curve(y_true_bin.ravel(), y_proba.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    # 4. Compute Macro-average ROC
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

    # 5. Plotting
    plt.figure(figsize=(12, 10))

    # Plot Micro & Macro Averages
    plt.plot(fpr["micro"], tpr["micro"],
             label=f'Micro-average (AUC = {roc_auc["micro"]:.2f})',
             color='deeppink', linewidth=2)

    plt.plot(fpr["macro"], tpr["macro"],
             label=f'Macro-average (AUC = {roc_auc["macro"]:.2f})',
             color='navy', linewidth=2)

    # Plot Per-Class Curves
    colors_cycle = cycle([
        'aqua', 'darkorange', 'cornflowerblue', 'green', 'red',
        'purple', 'gold', 'pink', 'brown', 'lime', 'magenta'
    ])

    for i, c in zip(range(n_classes), colors_cycle):
        plt.plot(fpr[i], tpr[i], color=c, lw=2,
                 label=f'{class_labels[i]} (AUC = {roc_auc[i]:.2f})')

    plt.plot([0, 1], [0, 1], 'k--', lw=2)  # Diagonal random guess line

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
    # Define inset position [x, y, width, height]
    inset_pos = [0.69, 0.55, 3, 3]
    x0, y0, w, h = inset_pos

    # Define area to zoom in (Top-Left corner usually)
    x1, x2 = 0, 0.05
    y1, y2 = 0.9, 1.0

    axins = inset_axes(ax, width=w, height=h, loc='lower left', bbox_to_anchor=(x0, y0, w, h),
                       bbox_transform=ax.transAxes)

    # Mark the zoomed area on main plot
    pad_x = (x2 - x1) * 0.3
    pad_y = (y2 - y1) * 0.3
    rect = Rectangle((x1 - pad_x, y1 - pad_y),
                     (x2 - x1) + 2 * pad_x,
                     (y2 - y1) + 2 * pad_y,
                     linewidth=1.5, edgecolor='red', facecolor='lightgray', alpha=0.3, linestyle='--')
    ax.add_patch(rect)

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
    plt.savefig(folder_path + "/multiclass_roc.png", dpi=300)
    plt.show()


# ======================================================================================================================
# ---------- Precision-Recall Curve ---------- #
def plot_multiclass_pr_curve(y_true, y_proba, class_labels):
    """
    Plots Precision-Recall curves for multi-class classification.
    """
    n_classes = len(class_labels)
    y_true_bin = label_binarize(y_true, classes=range(n_classes))
    colors_cycle = cycle(['navy', 'turquoise', 'darkorange', 'cornflowerblue', 'teal'])

    plt.figure(figsize=(10, 8))

    for i, color in zip(range(n_classes), colors_cycle):
        # Calculate P-R for each class
        precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_proba[:, i])
        ap_score = average_precision_score(y_true_bin[:, i], y_proba[:, i])

        plt.plot(recall, precision, color=color, lw=2,
                 label=f'{class_labels[i]} (AP = {ap_score:.2f})')

    plt.xlabel('Recall', fontsize=14)
    plt.ylabel('Precision', fontsize=14)
    plt.legend(loc="best")
    plt.grid(alpha=0.4)
    plt.show()


# ======================================================================================================================
# ---------- Grad-CAM Explanation ---------- #
def explain_with_gradcam(model, input_tensor, device, target_class=None, ax=None):
    """
    Generates Grad-CAM heatmap overlay for a specific input tensor.

    Args:
        input_tensor: Shape (1, C, H, W).
        ax: Matplotlib axis to plot on.
    Returns:
        img: The plot object.
        vmin, vmax: Range for color scaling.
    """
    import numpy as np
    model.eval()

    # 1. Select Target Layers for Gradient Calculation
    target_layers = [getattr(model, name) for name in layer1]

    # 2. Define Target Class
    if target_class is None:
        # If not specified, use the model's predicted class
        with torch.no_grad():
            output = model(input_tensor)
            predicted_class = output.argmax(dim=1).item()
            target_for_cam = [ClassifierOutputTarget(predicted_class)]
    else:
        target_for_cam = [ClassifierOutputTarget(target_class)]

    # 3. Generate Grad-CAM
    # Initialize GradCAM object
    cam = GradCAM(model=model, target_layers=target_layers, use_cuda=(device.type == 'cuda'))

    # Generate raw CAM. Shape: (Batch, H, W). We take [0, :]
    grayscale_cam = cam(input_tensor=input_tensor, targets=target_for_cam)[0, :]

    # 4. Prepare Background Image
    # Flatten/Reshape input for visualization.
    # Current input shape: (1, 1, 3, 4) -> Single channel
    # Extract the single channel map: (3, 4)
    single_channel_image = input_tensor.view(input_tensor.shape[2], input_tensor.shape[3]).cpu().numpy()

    # Create a pseudo-RGB image for `show_cam_on_image` by stacking the grayscale channel
    input_image_rgb = np.stack([single_channel_image] * 3, axis=-1)

    # Normalize background image to [0, 1] for visualization
    input_image_rgb = (input_image_rgb - np.min(input_image_rgb)) / (
            np.max(input_image_rgb) - np.min(input_image_rgb) + 1e-8)

    # Overlay Heatmap on Image
    cam_image = show_cam_on_image(input_image_rgb, grayscale_cam, use_rgb=True)

    # 5. Plotting
    plt.rcParams["font.family"] = "Times New Roman"
    axis_label_fontsize = 30
    tick_label_fontsize = 30

    # Parameter map layout (3x4 grid)
    feature_list = ['p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p15', 'p17', 'p21', 'p22', 'p24']
    feature_symbols = np.array(feature_list).reshape(3, 4)

    # --- Plot Subplot: Original Grayscale with Numeric Values ---
    vmin = np.percentile(single_channel_image, 5)
    vmax = np.percentile(single_channel_image, 95)
    img = ax.imshow(single_channel_image, cmap='gray')
    threshold = img.norm(single_channel_image.max()) / 2.
    H, W = single_channel_image.shape

    # Iterate over pixels to add text annotations
    for i in range(H):
        for j in range(W):
            symbol = feature_symbols[i, j]
            value = single_channel_image[i, j]
            text_content = f"{symbol}\n{value:.2f}"

            # Adaptive text color based on background brightness
            text_color = "white" if img.norm(value) < threshold else "black"

            ax.text(j, i, text_content,
                    ha="center", va="center",
                    color=text_color, fontsize=30, fontweight="bold")

    ax.set_xlabel("Width", fontsize=axis_label_fontsize)
    ax.set_ylabel("Height", fontsize=axis_label_fontsize)
    ax.tick_params(axis='both', which='major', labelsize=tick_label_fontsize)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_yticks([0, 1, 2])

    # Note: Other visualization options (Heatmap only, Overlay) are commented out in source

    return img, vmin, vmax


# ======================================================================================================================
# ---------- Main Execution Block ---------- #
if __name__ == '__main__':
    import numpy as np
    import pandas as pd  # Ensure pandas is imported

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DPFD_ACAM_ISimAM_TwoChannelFusion(In_channels, Conv_channels, Cbam_reduction).to(device)

    # 1. Load Pre-trained Model and Metrics
    checkpoint = torch.load("../model/best_model_" + str(Model_id) + ".pth")
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
    model.eval()  # Set to evaluation mode

    with torch.no_grad():
        # Restore metrics
        train_losses = checkpoint['train_loss']
        train_accs = checkpoint['train_acc']
        val_losses = checkpoint['val_loss']
        val_accs = checkpoint['val_acc']
        test_losses = checkpoint['test_loss']
        test_accs = checkpoint['test_acc']
        preds = checkpoint['test_preds']
        labels = checkpoint['test_labels']
        feats = checkpoint['test_feats']  # Features before classification layer for t-SNE

        # Load Data
        train_loader, val_loader, test_loader = read_data(Batch_size)

        # Collect all test data for specific sample selection later
        all_x = []
        all_y = []
        for input_batch, label_batch in test_loader:
            all_x.append(input_batch)
            all_y.append(label_batch)

        x = torch.cat(all_x, dim=0)  # Shape: [Total_Samples, C, H, W]
        y = torch.cat(all_y, dim=0)  # Shape: [Total_Samples]

        # ==============================================================================================================
        # Visualization 1: t-SNE (Feature Space Distribution)
        # ==============================================================================================================
        n_classes = 11
        plt.figure(figsize=(16, 9))

        # Initialize t-SNE
        tsne = TSNE(n_components=2, random_state=42, perplexity=6, learning_rate=100, n_iter=1000)
        features_2d = tsne.fit_transform(feats)

        # Define styles for scatter plot
        custom_markers = {'d1': 'o', 'd2': 's', 'd3': 'D', 'd4': '^', 'd5': 'v',
                          'd6': '<', 'd7': '>', 'd8': 'P', 'd9': '*', 'd10': 'p', 'd11': 'h'}
        custom_palette = {
            'd1': 'red', 'd2': 'blue', 'd3': 'green', 'd4': 'orange', 'd5': 'purple',
            'd6': 'cyan', 'd7': 'orchid', 'd8': 'darkviolet', 'd9': 'brown',
            'd10': 'pink', 'd11': 'gray'}

        # Map numeric labels (0-10) to class names (d1-d11)
        label_mapping = {i: f'd{i + 1}' for i in range(11)}

        # Create DataFrame for Seaborn
        df = pd.DataFrame({
            "x": features_2d[:, 0],
            "y": features_2d[:, 1],
            "label": labels
        })
        df["label"] = df["label"].map(label_mapping)

        ax = sns.scatterplot(
            data=df,
            x="x", y="y",
            hue="label", style="label",
            palette=custom_palette, markers=custom_markers,
            s=500  # Marker size
        )

        # Style box spines
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color('black')
            spine.set_linewidth(1.5)

        plt.tick_params(axis='x', labelsize=30)
        plt.tick_params(axis='y', labelsize=30)
        plt.xlabel('Thermal feature Dim 1', fontsize=30)
        plt.ylabel('Thermal feature Dim 2', fontsize=30)
        plt.tick_params(axis='both', which='both', direction='in')

        # Legend configuration
        legend = plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), fontsize=30, ncol=6)
        for handle in legend.legendHandles:
            handle.set_sizes([300])

        plt.grid(False)
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.tight_layout()
        plt.savefig(folder_path + "/tsne.png")
        plt.show()

        # ==============================================================================================================
        # Visualization 2: Confusion Matrix
        # ==============================================================================================================
        plt.figure(figsize=(16, 9))
        cm_matrix = confusion_matrix(labels, preds)
        ax = sns.heatmap(cm_matrix, annot=True, fmt="d", cmap="Blues",
                         xticklabels=range(1, 12), yticklabels=range(1, 12),  # d1-d11
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
        plt.savefig(folder_path + "/confusion_matrix.png")
        plt.show()

        # ==============================================================================================================
        # Visualization 3: Loss & Accuracy Curves
        # ==============================================================================================================
        # Loss Curve
        plt.figure(figsize=(16, 9))
        plt.plot(train_losses, label="Train loss", color='red', marker='o', linewidth=2)
        plt.plot(val_losses, label="Validation loss", color='green', marker='s', linewidth=2)
        plt.plot(test_losses, label="Test loss", color='blue', marker='^', linewidth=2)
        plt.xlabel("Epoch", fontsize=30)
        plt.ylabel("Loss", fontsize=30)
        plt.xticks(fontsize=30)
        plt.yticks(fontsize=30)
        plt.legend(fontsize=30)

        # Style axes
        ax = plt.gca()
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5)
        ax.spines['bottom'].set_linewidth(1.5)

        plt.rcParams['font.family'] = 'Times New Roman'
        plt.savefig(folder_path + "/loss_curve.png")
        plt.show()

        # Accuracy Curve
        plt.figure(figsize=(16, 9))
        plt.plot(train_accs, label='Train Accuracy', color='red', marker='o', linewidth=2)
        plt.plot(val_accs, label='Validation Accuracy', color='green', marker='s', linewidth=2)
        plt.plot(test_accs, label='Test Accuracy', color='blue', marker='^', linewidth=2)
        plt.xlabel('Epoch', fontsize=30)
        plt.ylabel('Accuracy', fontsize=30)
        plt.xticks(fontsize=30)
        plt.yticks(fontsize=30)
        plt.legend(fontsize=30)

        ax = plt.gca()
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_linewidth(1.5)
        ax.spines['bottom'].set_linewidth(1.5)

        plt.rcParams['font.family'] = 'Times New Roman'
        plt.savefig(folder_path + "/accuracy_curve.png")
        plt.show()

    # ==================================================================================================================
    # Evaluation Metrics: Classification Report & ROC
    # ==================================================================================================================
    class_names = [f'd{i}' for i in range(11)]

    # Calculate probabilities (Softmax)
    y_proba = F.softmax(feats, dim=1)

    # Classification Report
    report_dict = classification_report(labels, preds, target_names=class_names, output_dict=True)
    print("--- Classification Report ---")
    print(pd.DataFrame(report_dict).transpose())

    print(f"Accuracy: {report_dict['accuracy']:.4f}")
    print(f"Precision (macro): {report_dict['macro avg']['precision']:.4f}")
    print(f"Recall (macro): {report_dict['macro avg']['recall']:.4f}")
    print(f"F1-score (macro): {report_dict['macro avg']['f1-score']:.4f}")

    # Plot ROC Curve
    plot_multiclass_roc_curve(y_true=labels, y_proba=y_proba, class_labels=class_names)

    # SHAP Visualization (Optional)
    # explain_with_shap(model, test_loader, device)

    # ==================================================================================================================
    # Visualization 4: Multi-Sample Visual Explanations (Grad-CAM, Attention Weights)
    # ==================================================================================================================

    # 1. Sample Selection: Select one representative sample per class
    unique_classes = torch.unique(y)
    sample_indices = []

    # Define which sample index within the class to pick (e.g., the 0th sample of that class)
    sample_selection_idx = 0

    for cls in unique_classes:
        # Get all indices for the current class
        indices = (y == cls).nonzero(as_tuple=True)[0]
        if len(indices) > sample_selection_idx:
            sample_indices.append(indices[sample_selection_idx])

    # 2. Grad-CAM Visualization Grid
    rows, cols = 3, 4
    fig, axes = plt.subplots(rows, cols, figsize=(20, 15))
    axes = axes.flatten()

    target_layer_name = layer1[0]

    # Colormap definitions (for potential future use)
    light_purples = colors.LinearSegmentedColormap.from_list('light_purples', cm.Purples(np.linspace(0.1, 0.7, 256)))

    # Loop through selected samples
    for i, k in enumerate(sample_indices[:rows * cols]):
        input_tensor = x[k].unsqueeze(0)  # Shape: (1, C, H, W)

        # Generate Grad-CAM for the ground truth class y[k]
        img_grad_cam, vmin, vmax = explain_with_gradcam(model, input_tensor, device, y[k], axes[i])

    # Add Colorbar to the last subplot
    last_ax = axes[-1]
    cax2 = inset_axes(last_ax, width="10%", height="100%", loc='center',
                      bbox_to_anchor=(0, -0.2, 1, 1), bbox_transform=last_ax.transAxes, borderpad=0)
    norm = mpl.colors.Normalize(vmin=0, vmax=1)

    # Note: Using a generic cmap here as explain_with_gradcam uses grayscale mostly
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap='gray'), cax=cax2)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.ax.tick_params(labelsize=30)

    # Remove empty subplots
    for j in range(len(sample_indices), rows * cols):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.savefig(folder_path + "/Grad_cam_explanation.png")
    plt.show()

    # ==================================================================================================================
    # Visualization 5: Channel Attention Weights (Line Plot)
    # ==================================================================================================================
    ca_weight_list = []

    # Re-run forward pass to hook attention weights
    for input_batch, _ in test_loader:
        input_batch = input_batch.to(device)
        with torch.no_grad():
            _ = model(input_batch)
            # Extract weights from the model attribute (stored during forward)
            # Assuming 'layer2_1' is the name of the attribute storing Channel Attention weights
            ca_weight = getattr(model, layer2_1)  # Shape: [Batch, Channels]
            ca_weight_list.append(ca_weight)

    all_ca_weight = torch.cat(ca_weight_list, dim=0)

    # Plot
    fig1, axes1 = plt.subplots(rows, cols, figsize=(24, 16))
    axes1 = axes1.flatten()

    for i, k in enumerate(sample_indices):
        total_ca_weight = all_ca_weight[k].squeeze().cpu().numpy()
        ax = axes1[i]

        ax.plot(np.arange(len(total_ca_weight)), total_ca_weight, marker='o', linestyle='-', color='blue', linewidth=2)
        ax.set_xlabel("Channel Index", fontsize=30)
        ax.set_ylabel("Attention Weight", fontsize=30)

        ax.set_xlim(0, len(total_ca_weight) - 1)
        ax.set_ylim(0, 1.0)
        ax.set_xticks(np.arange(0, len(total_ca_weight), 40))  # Adjust step size
        ax.set_yticks(np.linspace(0, 1, 5))
        ax.tick_params(axis='both', labelsize=30)

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color('black')
            spine.set_linewidth(1.5)

    for j in range(len(sample_indices), rows * cols):
        fig1.delaxes(axes1[j])

    plt.tight_layout()
    plt.savefig(folder_path + "/ca_weight_curve.png")
    plt.show()

    # ==================================================================================================================
    # Visualization 6: SimAM Attention Maps
    # ==================================================================================================================
    # Access SimAM map for the last processed batch (requires model state)
    # Note: This logic assumes layer2_3 stores the SimAM map and only visualizes the last batch's first sample.
    att_map_simam = getattr(model, layer2_3).attention_map[0].cpu().numpy()  # Shape: (C, H, W)

    vmin = np.percentile(att_map_simam, 5)
    vmax = np.percentile(att_map_simam, 95)

    # Select representative channels to visualize
    selected_channels = [2, 6, 12, 30, 36, 42]
    rows_s, cols_s = 2, 3

    plt.figure(figsize=(18, 6))
    for idx, ch in enumerate(selected_channels):
        if ch < att_map_simam.shape[0]:
            plt.subplot(rows_s, cols_s, idx + 1)
            im = plt.imshow(att_map_simam[ch], cmap='Blues', vmin=vmin, vmax=vmax)
            plt.title(f"Channel {ch}", fontsize=12)
            plt.axis('off')

    # Shared colorbar
    cbar_ax = plt.gcf().add_axes([0.92, 0.15, 0.02, 0.7])
    plt.colorbar(im, cax=cbar_ax)

    plt.tight_layout()
    plt.savefig(folder_path + "/SimAM_map.png")
    plt.show()