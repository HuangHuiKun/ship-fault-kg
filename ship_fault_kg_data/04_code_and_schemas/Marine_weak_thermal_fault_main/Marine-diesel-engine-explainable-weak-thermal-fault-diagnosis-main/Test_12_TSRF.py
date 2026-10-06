import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import torch

# Import custom data interface
from Code.Test_12_1 import read_data

# ======================================================================================================================
# Global Plotting Configuration (Academic Style)
# ======================================================================================================================
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display


# ======================================================================================================================
# 1. Data Conversion Utility
# ======================================================================================================================
def dataloader_to_numpy(dataloader):
    """
    Converts a PyTorch DataLoader into Numpy arrays (X, y).

    Transformation:
        Input Tensor Shape: (Batch, 1, 3, 4) or (Batch, 1, 12)
        Output Array Shape: (Total_Samples, 12) - Flattened feature vector

    Args:
        dataloader (DataLoader): Source dataloader.

    Returns:
        tuple: (X_numpy, y_numpy)
    """
    all_X = []
    all_y = []

    for inputs, labels in dataloader:
        # Flatten inputs: (Batch, 1*3*4) -> (Batch, 12)
        # Random Forest requires 2D input (Samples, Features)
        flat_inputs = inputs.view(inputs.size(0), -1).numpy()
        labels = labels.numpy()

        all_X.append(flat_inputs)
        all_y.append(labels)

    # Concatenate all batches
    X = np.concatenate(all_X, axis=0)
    y = np.concatenate(all_y, axis=0)

    return X, y


# ======================================================================================================================
# 2. TSRF (Thermodynamic Simulation-assisted Random Forest) Workflow
# Methodology:
#   Utilizes Random Forest as an ensemble classifier to handle non-linear relationships
#   between thermodynamic parameters and fault types. Prioritizes explainability via Feature Importance.
# ======================================================================================================================
def train_tsrf():
    # --- Step 1: Data Preparation ---
    print("Step 1: Loading and Converting Data...")
    train_loader, val_loader, test_loader = read_data()

    # Convert Tensor DataLoaders to Numpy Arrays for Scikit-Learn
    X_train, y_train = dataloader_to_numpy(train_loader)
    X_val, y_val = dataloader_to_numpy(val_loader)
    X_test, y_test = dataloader_to_numpy(test_loader)

    print(f"Training Set Shape: {X_train.shape}, Label Shape: {y_train.shape}")

    # --- Step 2: Model Initialization ---
    # Random Forest Hyperparameters:
    # n_estimators: Number of trees (Stability)
    # max_depth: Maximum depth of trees (Prevent Overfitting)
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,  # Allow full growth (or set int to prune)
        min_samples_split=2,
        random_state=42,  # Ensure reproducibility
        n_jobs=-1  # Use all available CPU cores
    )

    # --- Step 3: Training ---
    print("Step 2: Training Random Forest Model (TSRF Base)...")
    rf_model.fit(X_train, y_train)

    # --- Step 4: Evaluation ---
    print("Step 3: Evaluating Performance...")

    # Validation
    val_preds = rf_model.predict(X_val)
    val_acc = accuracy_score(y_val, val_preds)
    print(f"Validation Accuracy: {val_acc:.4f}")

    # Testing
    test_preds = rf_model.predict(X_test)
    test_acc = accuracy_score(y_test, test_preds)
    print(f"Test Accuracy: {test_acc:.4f}")

    print("\n--- Classification Report (Test Set) ---")
    # digits=4 ensures high precision for academic tables
    print(classification_report(y_test, test_preds, digits=4))

    # ==================================================================================================================
    # 3. Explainability Analysis
    # Key Contribution: Analyzing which thermodynamic parameters trigger specific faults.
    # ==================================================================================================================
    print("\nStep 4: Explainability Analysis (Feature Importance)...")

    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]  # Sort descending

    # Define Feature Names (Map these to physical parameters like P_max, T_exh, etc.)
    # Example: feature_names = ['T_cyl', 'P_max', 'T_exh', ...]
    feature_names = [f"Param_{i}" for i in range(12)]

    # Print Top 5 Critical Features
    print("Top 5 Critical Features for Diagnosis:")
    for f in range(5):
        idx = indices[f]
        print(f"{f + 1}. {feature_names[idx]}: {importances[idx]:.4f}")

    # --- Visualization 1: Feature Importance ---
    plt.figure(figsize=(12, 8))

    # Create Bar Plot
    plt.bar(range(X_train.shape[1]), importances[indices], align="center", color='steelblue', alpha=0.8)

    # Styling
    plt.title("Feature Importance Analysis (TSRF)", fontsize=20, pad=20)
    plt.xticks(range(X_train.shape[1]), [feature_names[i] for i in indices], rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.xlabel("Thermodynamic Parameters", fontsize=16)
    plt.ylabel("Importance Score (Gini Impurity)", fontsize=16)

    plt.tight_layout()
    plt.show()

    # --- Visualization 2: Confusion Matrix ---
    cm = confusion_matrix(y_test, test_preds)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                annot_kws={"size": 14}, cbar_kws={"shrink": 0.8})

    plt.title("Confusion Matrix (TSRF)", fontsize=20, pad=20)
    plt.xlabel("Predicted Condition", fontsize=16)
    plt.ylabel("Actual Condition", fontsize=16)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    train_tsrf()