#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TSRF - Engine Health State Classification using Machine Learning

This script trains and compares three machine learning models (KNN, Random Forest, SVM)
for classifying engine health states based on thermodynamic sensor data.

Usage:
    python main.py [--use-feature-selection] [--random-state 42] [--test-size 216]

Author: Graduate Research Project
"""

import os
import sys
import argparse
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_loader import load_data, prepare_data, get_class_names
from src.models import KNNClassifier, RandomForestModel, SVMClassifier, compare_models
from src.visualization import plot_confusion_matrix, plot_roc_curve, plot_model_comparison
from src.shap_analysis import SHAPAnalyzer

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


def print_separator(title: str = None):
    """Print a separator line."""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def print_evaluation_results(model_name: str, results: dict, class_names: list):
    """Print evaluation results in a formatted way."""
    print(f"\n[{model_name}] Evaluation Results:")
    print("-" * 50)
    
    # Print accuracy
    print(f"Accuracy: {results['accuracy']:.4f} ({results['accuracy']*100:.2f}%)")
    
    # Print AUC scores
    print("\nAUC Scores by Class:")
    for class_name, auc in results['auc_scores'].items():
        print(f"  {class_name}: {auc:.4f}")
    
    # Print classification report as table
    report = results['classification_report']
    print("\nClassification Report:")
    print(f"{'Class':<12} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
    print("-" * 52)
    
    for class_name in class_names:
        if class_name in report:
            metrics = report[class_name]
            print(f"{class_name:<12} {metrics['precision']*100:>9.2f}% {metrics['recall']*100:>9.2f}% "
                  f"{metrics['f1-score']*100:>9.2f}% {int(metrics['support']):>10}")
    
    print("-" * 52)
    # Print averages
    for avg_type in ['macro avg', 'weighted avg']:
        if avg_type in report:
            metrics = report[avg_type]
            print(f"{avg_type:<12} {metrics['precision']*100:>9.2f}% {metrics['recall']*100:>9.2f}% "
                  f"{metrics['f1-score']*100:>9.2f}% {int(metrics['support']):>10}")


def train_and_evaluate_models(X_train, X_test, y_train, y_test, class_names, output_dir, random_state):
    """Train and evaluate all three models."""
    
    results = {}
    
    # ========== 1. KNN Classifier ==========
    print_separator("Training KNN Classifier with Grid Search")
    
    knn = KNNClassifier(random_state=random_state, n_splits=10)
    knn.train(X_train, y_train, use_grid_search=True)
    
    knn_results = knn.evaluate(X_test, y_test, class_names)
    results['KNN'] = knn_results
    
    print_evaluation_results("KNN", knn_results, class_names)
    
    # Plot confusion matrix and ROC curve
    plot_confusion_matrix(y_test, knn_results['y_pred'], class_names, "KNN", output_dir)
    plot_roc_curve(y_test, knn_results['y_pred_prob'], len(class_names), class_names, "KNN", output_dir)
    
    # ========== 2. Random Forest Classifier ==========
    print_separator("Training Random Forest Classifier")
    
    rf = RandomForestModel(n_estimators=20, random_state=random_state)
    rf.train(X_train, y_train)
    
    rf_results = rf.evaluate(X_test, y_test, class_names)
    results['Random Forest'] = rf_results
    
    print_evaluation_results("Random Forest", rf_results, class_names)
    
    # Plot confusion matrix and ROC curve
    plot_confusion_matrix(y_test, rf_results['y_pred'], class_names, "RF", output_dir)
    plot_roc_curve(y_test, rf_results['y_pred_prob'], len(class_names), class_names, "RF", output_dir)
    
    # ========== 3. SVM Classifier ==========
    print_separator("Training SVM Classifier")
    
    svm = SVMClassifier(kernel='linear', random_state=random_state)
    svm.train(X_train, y_train)
    
    svm_results = svm.evaluate(X_test, y_test, class_names)
    results['SVM'] = svm_results
    
    print_evaluation_results("SVM", svm_results, class_names)
    
    # Plot confusion matrix and ROC curve
    plot_confusion_matrix(y_test, svm_results['y_pred'], class_names, "SVM", output_dir)
    plot_roc_curve(y_test, svm_results['y_pred_prob'], len(class_names), class_names, "SVM", output_dir)
    
    return results


def main():
    """Main function to run the complete training and evaluation pipeline."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Engine Health State Classification')
    parser.add_argument('--use-feature-selection', action='store_true',
                       help='Use feature selection to reduce dimensionality')
    parser.add_argument('--random-state', type=int, default=20,
                       help='Random seed for reproducibility (default: 20)')
    parser.add_argument('--test-size', type=int, default=216,
                       help='Number of samples for test set (default: 216)')
    parser.add_argument('--enable-shap', action='store_true',
                       help='Enable SHAP analysis for model interpretability')
    parser.add_argument('--shap-classes', type=str, default=None,
                       help='Comma-separated class indices for SHAP analysis (e.g., "0,2,4"). If not specified, analyzes all classes.')
    args = parser.parse_args()
    
    # Configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
    
    print_separator("TSRF - Engine Health State Classification")
    print(f"\nConfiguration:")
    print(f"  - Data directory: {DATA_DIR}")
    print(f"  - SHAP analysis: {args.enable_shap}")
    print(f"  - Output directory: {OUTPUT_DIR}")
    print(f"  - Feature selection: {args.use_feature_selection}")
    print(f"  - Random state: {args.random_state}")
    print(f"  - Test size: {args.test_size}")
    print(f"  - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========== Step 1: Load Data ==========
    print_separator("Loading Data")
    
    X, y, label_encoder, feature_mapping = load_data(
        DATA_DIR, 
        use_feature_selection=args.use_feature_selection
    )
    
    print(f"Dataset shape: {X.shape}")
    print(f"Number of classes: {len(label_encoder.classes_)}")
    print(f"Class distribution:")
    for i, cls in enumerate(label_encoder.classes_):
        count = (y == i).sum()
        print(f"  - {cls} (F{i}): {count} samples")
    
    print(f"\nFeature mapping:")
    for orig, numbered in list(feature_mapping.items())[:5]:
        print(f"  - {numbered}: {orig}")
    print(f"  ... ({len(feature_mapping)} features total)")
    
    # ========== Step 2: Prepare Data ==========
    print_separator("Preparing Data")
    
    X_train, X_test, y_train, y_test, scaler = prepare_data(
        X, y,
        test_size=args.test_size,
        random_state=args.random_state,
        normalize=True
    )
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    print("Data normalized using StandardScaler")
    
    # Get class names
    class_names = get_class_names(label_encoder)
    
    # ========== Step 3: Train and Evaluate Models ==========
    all_results = train_and_evaluate_models(
        X_train, X_test, y_train, y_test,
        class_names, OUTPUT_DIR, args.random_state
    )
    
    # ========== Step 4: Compare Models ==========
    print_separator("Model Comparison Summary")
    
    comparison_df = compare_models(all_results)
    
    # Print comparison table
    print("\n" + comparison_df.to_string(index=False))
    
    # Save comparison to CSV
    comparison_path = os.path.join(OUTPUT_DIR, "model_comparison.csv")
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\nComparison results saved to {comparison_path}")
    
    # Plot comparison chart
    plot_model_comparison(comparison_df, OUTPUT_DIR)
    
    # ========== Step 5: SHAP Analysis (Optional) ==========
    if args.enable_shap:
        print_separator("SHAP Interpretability Analysis")
        
        # Use Random Forest model for SHAP (best performing model)
        best_model_name = comparison_df.loc[comparison_df['Accuracy'].idxmax(), 'Model']
        print(f"\nPerforming SHAP analysis on: {best_model_name}")
        
        # Get the Random Forest model
        rf_model = RandomForestModel(n_estimators=20, random_state=args.random_state)
        rf_model.train(X_train, y_train)
        
        # Parse class indices if provided
        if args.shap_classes:
            class_indices = [int(x.strip()) for x in args.shap_classes.split(',')]
            print(f"Analyzing classes: {class_indices}")
        else:
            class_indices = None
            print("Analyzing all classes")
        
        # Create SHAP analyzer
        shap_analyzer = SHAPAnalyzer(
            model=rf_model.model,
            X_train=X_train,
            X_test=X_test,
            feature_names=list(X.columns) if hasattr(X, 'columns') else None
        )
        
        # Generate all SHAP plots
        shap_analyzer.generate_all_plots(
            class_indices=class_indices,
            output_dir=OUTPUT_DIR,
            sample_idx=0
        )
    
    # ========== 
    # ========== Final Summary ==========
    print_separator("Training Complete")
    
    # Find best model
    best_model_idx = comparison_df['Accuracy'].idxmax()
    best_model = comparison_df.loc[best_model_idx, 'Model']
    best_accuracy = comparison_df.loc[best_model_idx, 'Accuracy']
    
    print(f"\nBest performing model: {best_model}")
    print(f"Best accuracy: {best_accuracy:.4f} ({best_accuracy*100:.2f}%)")
    print(f"\nAll outputs saved to: {OUTPUT_DIR}")
    print("\nGenerated files:")
    for f in os.listdir(OUTPUT_DIR):
        print(f"  - {f}")
    
    return all_results, comparison_df


if __name__ == "__main__":
    results, comparison = main()
