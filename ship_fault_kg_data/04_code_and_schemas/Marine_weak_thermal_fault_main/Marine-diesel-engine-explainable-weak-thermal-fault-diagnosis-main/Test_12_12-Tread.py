import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import os

# ======================================================================================================================
# 0. Global Configuration (Academic Style)
# ======================================================================================================================
# Set font family to Times New Roman for academic publication standards
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

# Define save path (Modify as needed)
save_dir = r"D:\PycharmProjects\Diesel_engine_thermal_fault_diagnosis\figure5"
os.makedirs(save_dir, exist_ok=True)

# ======================================================================================================================
# 1. Data Preparation
# ======================================================================================================================
print("Step 1: Preparing data...")

try:
    # Load dataset
    data = pd.read_csv('../data/100%_engine_dataset.csv')
    print("Successfully loaded CSV file.")

    X = data.drop('y_label', axis=1)
    y = data['y_label']
    N_CLASSES = y.nunique()
    print(f"Data loaded. Number of classes: {N_CLASSES}")

    # --- Data Augmentation: Noise Injection ---
    noise_level = 0.02
    noise = X.values * noise_level * np.random.randn(*X.shape)
    X = X + noise
    X = pd.DataFrame(X, columns=data.drop('y_label', axis=1).columns)
    print(f"Added {noise_level * 100}% Gaussian noise for robustness.")

    # --- Feature Selection ---
    # Select specific sensor indices based on domain knowledge
    selected_features_indices = [4, 5, 6, 7, 8, 9, 10, 14, 16, 20, 21, 23]
    X_selected = X.iloc[:, selected_features_indices]

except FileNotFoundError:
    print("Error: CSV file not found. Generating dummy data for demonstration.")
    # Dummy data generation (Fallback)
    dummy_n = 300
    X_dummy = np.random.randn(dummy_n, 25)
    X_dummy = pd.DataFrame(X_dummy, columns=[f'Sensor_{i}' for i in range(25)])
    y = pd.Series(np.random.randint(0, 3, dummy_n), name='y_label')
    X_selected = X_dummy.iloc[:, [4, 5, 6, 7, 8, 9, 10, 14, 16, 20, 21, 23]]
    N_CLASSES = 3

# --- Rename Features ---
new_feature_names = ['p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p15', 'p17', 'p21', 'p22', 'p24']
X_selected.columns = new_feature_names
print("Features renamed.")

# ======================================================================================================================
# 2. Normalization & PCA
# ======================================================================================================================
print("\nStep 2: Performing Normalization and PCA...")

# 2.1 Normalization (Min-Max)
# PCA is sensitive to the scale of features. Normalization ensures all features contribute equally.
scaler = MinMaxScaler()
X_norm = scaler.fit_transform(X_selected)

# 2.2 PCA Dimensionality Reduction
pca = PCA(n_components=3)
X_pca_3d = pca.fit_transform(X_norm)

# Calculate Explained Variance Ratio
evr = pca.explained_variance_ratio_
print(f"Explained Variance -> PC1: {evr[0]:.2%}, PC2: {evr[1]:.2%}, PC3: {evr[2]:.2%}")
print(f"Total Variance Explained: {sum(evr):.2%}")

# ======================================================================================================================
# 3. Visualization
# ======================================================================================================================
# Initialize large figure
fig = plt.figure(figsize=(24, 12))

# --- Subplot 1: 3D Scatter Plot (PCA Space) ---
ax1 = fig.add_subplot(121, projection='3d')

unique_labels = np.unique(y)
markers = ['o', 's', '^', 'D', 'x', 'v', '<', '>', 'p', '*', 'h']
colors_list = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))

for i, label in enumerate(unique_labels):
    mask = (y == label)
    ax1.scatter(X_pca_3d[mask, 0], X_pca_3d[mask, 1], X_pca_3d[mask, 2],
                label=f'Class {label}',
                c=[colors_list[i]],
                marker=markers[i % len(markers)],
                s=80, alpha=0.8, edgecolor='k', linewidth=0.5)

# Axis Labels
ax1.set_xlabel(f'PC 1 ({evr[0]:.1%})', fontsize=30, labelpad=20)
ax1.set_ylabel(f'PC 2 ({evr[1]:.1%})', fontsize=30, labelpad=20)
ax1.set_zlabel(f'PC 3 ({evr[2]:.1%})', fontsize=30, labelpad=20)
ax1.set_title('3D PCA Visualization', fontsize=35, pad=30)

# Tick Settings
ax1.tick_params(axis='both', which='major', labelsize=20)
for t in ax1.xaxis.get_major_ticks(): t.label.set_fontsize(25)
for t in ax1.yaxis.get_major_ticks(): t.label.set_fontsize(25)
for t in ax1.zaxis.get_major_ticks(): t.label.set_fontsize(25)

# Legend
ax1.legend(fontsize=25, loc='upper left', bbox_to_anchor=(-0.1, 1), title="Classes", title_fontsize=25)
ax1.view_init(elev=30, azim=-60)

# --- Subplot 2: Loadings Heatmap (Feature Weights) ---
ax2 = fig.add_subplot(122)

components = pca.components_
# Using vmin=-1, vmax=1 allows 'coolwarm' to correctly show negative (blue) and positive (red) correlations
im = ax2.imshow(components, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)

# Colorbar
cbar = plt.colorbar(im, ax=ax2)
cbar.ax.tick_params(labelsize=25)
cbar.set_label('Contribution Weight', size=30)

# Axis Labels
ax2.set_yticks([0, 1, 2])
ax2.set_yticklabels(['PC 1', 'PC 2', 'PC 3'], fontsize=30)
ax2.set_xticks(range(len(new_feature_names)))
ax2.set_xticklabels(new_feature_names, rotation=45, ha='right', fontsize=30)

ax2.set_title('PCA Loadings (Feature Weights)', fontsize=35, pad=20)

# Annotate heatmap with values
for i in range(components.shape[0]):
    for j in range(components.shape[1]):
        # Dynamic text color based on value intensity for readability
        val = components[i, j]
        text_color = "white" if abs(val) > 0.5 else "black"
        text = ax2.text(j, i, f"{val:.2f}",
                        ha="center", va="center", color=text_color, fontsize=25)

plt.tight_layout()

# Save and Show
save_file = os.path.join(save_dir, "PCA_Trend_Analysis.png")
plt.savefig(save_file, dpi=300)
print(f"Plot saved to: {save_file}")
plt.show()

# ======================================================================================================================
# 4. Automated Analysis Report
# ======================================================================================================================
print("\n--- Analysis Report ---")
pc1_weights = np.abs(components[0])
top_feature_idx = np.argmax(pc1_weights)
print(f"1. Dominant Feature for PC 1: {new_feature_names[top_feature_idx]} (Weight: {components[0][top_feature_idx]:.3f})")
print(f"   - This feature contributes most significantly to the variance along the first principal component.")