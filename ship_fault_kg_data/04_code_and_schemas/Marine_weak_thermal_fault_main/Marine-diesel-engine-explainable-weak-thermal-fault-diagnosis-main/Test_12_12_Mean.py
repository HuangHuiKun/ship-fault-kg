import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler  # Import normalization tool

# ======================================================================================================================
# 1. Data Preparation
# ======================================================================================================================
print("Step 1: Preparing data...")
try:
    # Load dataset
    data = pd.read_csv('../data/100%_engine_dataset.csv')
except FileNotFoundError:
    print("Error: CSV file not found.")
    exit()

# Separate features and labels
X = data.drop('y_label', axis=1)
y = data['y_label']
N_CLASSES = y.nunique()

# --- Data Augmentation: Noise Injection ---
# Add small Gaussian noise to simulate sensor fluctuations and improve robustness
noise_level = 0.02
noise = X.values * noise_level * np.random.randn(*X.shape)
X = X + noise

# --- Feature Selection ---
# Select 12 specific thermal parameters based on domain knowledge
selected_features_indices = np.array([4, 5, 6, 7, 8, 9, 10, 14, 16, 20, 21, 23])
X_selected = X.iloc[:, selected_features_indices]

# --- Column Renaming ---
# Rename columns to standard parameter codes (p5, p6, etc.)
new_feature_names = ['p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p15', 'p17', 'p21', 'p22', 'p24']
X_selected.columns = new_feature_names

# ----------------------------------------------------------------------------------------------------------------------
# [New Step]: Data Normalization (Min-Max)
# ----------------------------------------------------------------------------------------------------------------------
# Scale each feature to the [0, 1] range to eliminate magnitude differences.
# This ensures that features with large values (e.g., Pressure) don't visually dominate
# features with small values (e.g., Temperature ratios).
scaler = MinMaxScaler()
X_normalized_values = scaler.fit_transform(X_selected)

# Reconstruct DataFrame (keeping the original column names)
X_selected = pd.DataFrame(X_normalized_values, columns=new_feature_names)

print("Data normalized to range [0, 1].")

# ======================================================================================================================
# 2. Plotting Configuration (Academic Style: Times New Roman)
# ======================================================================================================================

# --- Prepare Plotting Data ---
# Aggregate data: Calculate the mean value of each feature for every health state
plot_df = X_selected.copy()
plot_df['Health_State'] = y.values
mean_df = plot_df.groupby('Health_State').mean()

# --- Global Font Settings ---
# Set font family to Times New Roman for academic publication standards
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']

# Set up a large canvas for high resolution
plt.figure(figsize=(20, 12))
sns.set_style("whitegrid")  # Clean background with grid

# Define a distinct color palette for N classes
colors = plt.cm.tab20(np.linspace(0, 1, N_CLASSES))

# --- Plotting Loop ---
# Iterate through each health state and plot its mean feature vector
for i, state in enumerate(mean_df.index):
    plt.plot(
        mean_df.columns,
        mean_df.loc[state],
        marker='o',
        markersize=12,   # Large markers for visibility
        linewidth=3,     # Thick lines
        label=f'State {state}',
        color=colors[i]
    )

# ======================================================================================================================
# 3. Labeling and Styling
# ======================================================================================================================

# Note: Title is commented out as figure captions are usually used in papers
# plt.title(f'Normalized Mean Values of Features across {N_CLASSES} Health States', fontsize=35, fontname='Times New Roman', pad=25)

plt.xlabel('Feature', fontsize=30, fontname='Times New Roman', labelpad=15)
# Updated Y-axis label to reflect normalization
plt.ylabel('Normalized Mean Value', fontsize=30, fontname='Times New Roman', labelpad=15)

# --- Tick Settings ---
plt.tick_params(axis='both', which='major', labelsize=30)
plt.xticks(fontname='Times New Roman')
plt.yticks(fontname='Times New Roman')

# --- Legend Settings ---
# Place legend outside the plot area to avoid occlusion
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=25, title="Health States", title_fontsize=25)

# Add grid lines for readability
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()

# --- Save and Show ---
save_path = fr"D:\PycharmProjects\Diesel_engine_thermal_fault_diagnosis\figure5\Mean.png"
# Create directory if strictly necessary, though usually handled externally
# import os; os.makedirs(os.path.dirname(save_path), exist_ok=True)

plt.savefig(save_path, dpi=300)
print(f"Plot saved successfully at: {save_path}")
plt.show()