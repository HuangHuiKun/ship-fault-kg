"""
Visualization module for classification results.

This module provides functions for plotting confusion matrices and ROC curves.
"""

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
from itertools import cycle
from typing import List, Optional
import os


def plot_confusion_matrix(
    y_true,
    y_pred,
    class_names: List[str],
    model_name: str,
    output_dir: str = 'outputs',
    figsize: tuple = (10, 10),
    save: bool = True
) -> None:
    """
    Plot and save confusion matrix.
    
    Args:
        y_true: True labels.
        y_pred: Predicted labels.
        class_names: List of class names.
        model_name: Name of the model (used in filename).
        output_dir: Directory to save the plot.
        figsize: Figure size.
        save: If True, saves the plot to file.
    """
    # Generate confusion matrix
    conf_matrix = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=conf_matrix, display_labels=class_names)
    
    plt.rcParams['font.family'] = 'Times New Roman'
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    disp.plot(ax=ax, cmap=plt.cm.Blues, values_format='d', colorbar=False, include_values=False)
    
    # Add colorbar with custom styling
    cbar = fig.colorbar(ax.images[0], ax=ax, shrink=0.7)
    for label in cbar.ax.get_yticklabels():
        label.set_fontproperties(font_manager.FontProperties(family='Times New Roman', size=20, weight='bold'))
    
    # Add text annotations with adaptive colors
    for i in range(conf_matrix.shape[0]):
        for j in range(conf_matrix.shape[1]):
            value = conf_matrix[i, j]
            text_color = "black" if value < 0.5 * conf_matrix.max() else "white"
            plt.text(j, i, value, ha='center', va='center', color=text_color, 
                    fontsize=20, fontproperties='Times New Roman')
    
    # Set labels and title
    plt.title('Confusion Matrix', fontsize=24, fontweight='bold')
    plt.xlabel('Predicted label', fontsize=20, fontweight='bold')
    plt.ylabel('True label', fontsize=20, fontweight='bold')
    plt.xticks(fontsize=16, fontweight='bold')
    plt.yticks(fontsize=16, fontweight='bold')
    
    if save:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"confusion_matrix_{model_name}.png")
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        print(f"Confusion matrix saved to {filepath}")
    
    plt.close()


def plot_roc_curve(
    y_true,
    y_pred_prob,
    n_classes: int,
    class_names: List[str],
    model_name: str,
    output_dir: str = 'outputs',
    figsize: tuple = (10, 10),
    save: bool = True
) -> dict:
    """
    Plot and save ROC curve for multiclass classification.
    
    Args:
        y_true: True labels.
        y_pred_prob: Predicted probabilities.
        n_classes: Number of classes.
        class_names: List of class names.
        model_name: Name of the model (used in filename).
        output_dir: Directory to save the plot.
        figsize: Figure size.
        save: If True, saves the plot to file.
    
    Returns:
        Dictionary with AUC scores for each class.
    """
    # Binarize labels
    y_true_bin = label_binarize(y_true, classes=range(n_classes))
    
    # Calculate ROC curve and AUC for each class
    fpr = {}
    tpr = {}
    roc_auc = {}
    
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_true_bin[:, i], y_pred_prob[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])
    
    # Calculate micro-average ROC curve
    fpr["micro"], tpr["micro"], _ = roc_curve(y_true_bin.ravel(), y_pred_prob.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
    
    # Plot
    plt.figure(figsize=figsize)
    colors = cycle(['aqua', 'darkorange', 'cornflowerblue', 'red', 'purple', 'green'])
    
    for i, color in zip(range(n_classes), colors):
        plt.plot(fpr[i], tpr[i], color=color, lw=2,
                label=f'Class {class_names[i]} (AUC = {roc_auc[i]:0.2f})')
    
    # Plot micro-average ROC curve
    plt.plot(fpr["micro"], tpr["micro"],
            label=f'Micro-average ROC curve (AUC = {roc_auc["micro"]:0.2f})',
            color='deeppink', linestyle=':', linewidth=4)
    
    # Add diagonal line
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=14)
    plt.ylabel('True Positive Rate', fontsize=14)
    plt.title(f'ROC Curve - {model_name}', fontsize=16)
    
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_linewidth(2)
    
    plt.legend(loc="lower right", fontsize=12, frameon=False)
    plt.grid(alpha=0.3)
    
    if save:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, f"ROC_{model_name}.png")
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        print(f"ROC curve saved to {filepath}")
        
        # Save ROC data to CSV
        _save_roc_data(fpr, tpr, roc_auc, n_classes, class_names, model_name, output_dir)
    
    plt.close()
    
    return roc_auc


def _save_roc_data(fpr, tpr, roc_auc, n_classes, class_names, model_name, output_dir):
    """Save ROC data to CSV file."""
    roc_data = []
    
    for i in range(n_classes):
        for j in range(len(fpr[i])):
            roc_data.append({
                "Class": f"Class {class_names[i]}",
                "FPR": fpr[i][j],
                "TPR": tpr[i][j],
                "AUC": roc_auc[i]
            })
    
    # Add micro-average data
    for j in range(len(fpr["micro"])):
        roc_data.append({
            "Class": "Micro-average",
            "FPR": fpr["micro"][j],
            "TPR": tpr["micro"][j],
            "AUC": roc_auc["micro"]
        })
    
    roc_df = pd.DataFrame(roc_data)
    csv_filepath = os.path.join(output_dir, f"ROC_data_{model_name}.csv")
    roc_df.to_csv(csv_filepath, index=False)
    print(f"ROC data saved to {csv_filepath}")


def plot_model_comparison(comparison_df: pd.DataFrame, output_dir: str = 'outputs', save: bool = True):
    """
    Plot comparison of model accuracies.
    
    Args:
        comparison_df: DataFrame with model comparison metrics.
        output_dir: Directory to save the plot.
        save: If True, saves the plot to file.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Accuracy comparison
    ax1 = axes[0]
    models = comparison_df['Model'].tolist()
    accuracies = comparison_df['Accuracy'].tolist()
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    
    bars = ax1.bar(models, accuracies, color=colors[:len(models)])
    ax1.set_ylabel('Accuracy', fontsize=12)
    ax1.set_title('Model Accuracy Comparison', fontsize=14, fontweight='bold')
    ax1.set_ylim([0, 1.0])
    
    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{acc:.2%}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Plot 2: F1-Score comparison
    ax2 = axes[1]
    x = np.arange(len(models))
    width = 0.35
    
    macro_f1 = comparison_df['Macro Avg F1'].tolist()
    weighted_f1 = comparison_df['Weighted Avg F1'].tolist()
    
    bars1 = ax2.bar(x - width/2, macro_f1, width, label='Macro Avg F1', color='#9b59b6')
    bars2 = ax2.bar(x + width/2, weighted_f1, width, label='Weighted Avg F1', color='#f39c12')
    
    ax2.set_ylabel('F1-Score', fontsize=12)
    ax2.set_title('F1-Score Comparison', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(models)
    ax2.legend()
    ax2.set_ylim([0, 1.0])
    
    plt.tight_layout()
    
    if save:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, "model_comparison.png")
        plt.savefig(filepath, format='png', dpi=300, bbox_inches='tight')
        print(f"Model comparison plot saved to {filepath}")
    
    plt.close()
