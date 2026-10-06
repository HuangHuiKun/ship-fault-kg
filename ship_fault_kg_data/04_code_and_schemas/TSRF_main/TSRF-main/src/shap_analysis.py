"""
SHAP (SHapley Additive exPlanations) Analysis Module

This module provides comprehensive SHAP analysis for model interpretability,
including Waterfall, Beeswarm, Interaction, and Dependence plots.
"""

import shap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from typing import Optional, List


class SHAPAnalyzer:
    """
    SHAP analyzer for tree-based models (Random Forest, XGBoost, etc.)
    """
    
    def __init__(self, model, X_train, X_test, feature_names: Optional[List[str]] = None):
        """
        Initialize SHAP analyzer.
        
        Args:
            model: Trained tree-based model.
            X_train: Training data (used for background).
            X_test: Test data (for explanation).
            feature_names: List of feature names.
        """
        self.model = model
        self.X_train = X_train
        self.X_test = X_test
        
        # Store original feature names for mapping
        self.original_feature_names = feature_names
        
        # Convert to DataFrame if needed
        if isinstance(X_train, np.ndarray):
            if feature_names is None:
                feature_names = [f'P{i+1:02d}' for i in range(X_train.shape[1])]
            self.X_train = pd.DataFrame(X_train, columns=feature_names)
            self.X_test = pd.DataFrame(X_test, columns=feature_names)
        
        # Create mapping from original names to P01-P14 format
        self.feature_name_to_code = {}
        self.feature_code_to_name = {}
        if self.original_feature_names:
            for i, name in enumerate(self.original_feature_names):
                code = f'P{i+1:02d}'
                self.feature_name_to_code[name] = code
                self.feature_code_to_name[code] = name
        
        # Rename columns to P01-P14 format for SHAP analysis
        feature_codes = [f'P{i+1:02d}' for i in range(self.X_train.shape[1])]
        self.X_train.columns = feature_codes
        self.X_test.columns = feature_codes
        
        # Global plotting settings
        plt.rcParams['font.family'] = 'Arial'
        plt.rcParams['font.size'] = 24
        plt.rcParams['axes.unicode_minus'] = False
        
        # Calculate SHAP values
        print("Calculating SHAP values (this may take a while)...")
        self.explainer_tree = shap.TreeExplainer(self.model)
        self.shap_values_numpy = self.explainer_tree.shap_values(self.X_train)
        
        # For waterfall plot
        self.explainer_obj = shap.Explainer(self.model, self.X_test)
        self.shap_values_obj = self.explainer_obj(self.X_test)
        
        print("SHAP values calculated successfully!")
    
    def plot_waterfall(
        self, 
        class_idx: int = 0, 
        sample_idx: int = 0, 
        max_display: int = 9,
        output_dir: str = 'outputs',
        save: bool = True
    ):
        """
        Plot waterfall plot for a single sample.
        
        Args:
            class_idx: Target class index.
            sample_idx: Sample index to explain.
            max_display: Maximum number of features to display.
            output_dir: Directory to save the plot.
            save: If True, saves the plot.
        """
        plt.figure(figsize=(10, 8))
        
        shap.plots.waterfall(
            self.shap_values_obj[sample_idx, :, class_idx],
            max_display=max_display,
            show=False
        )
        
        # Customize style
        ax = plt.gca()
        ax.set_xlabel(ax.get_xlabel(), fontsize=28)
        ax.set_ylabel(ax.get_ylabel(), fontsize=28)
        ax.tick_params(labelsize=20)
        ax.spines['bottom'].set_linewidth(3)
        
        plt.title(f'SHAP Waterfall Plot - Class F{class_idx}, Sample {sample_idx}', 
                 fontsize=24, pad=20)
        
        if save:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f'SHAP_waterfall_F{class_idx}_sample{sample_idx}.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Waterfall plot saved to {filepath}")
        
        plt.close()
    
    def plot_beeswarm(
        self,
        class_idx: int = 0,
        output_dir: str = 'outputs',
        save: bool = True
    ):
        """
        Plot beeswarm plot showing global feature importance.
        
        Args:
            class_idx: Target class index.
            output_dir: Directory to save the plot.
            save: If True, saves the plot.
            cmap: Colormap for the plot.
        """
        plt.figure(figsize=(10, 8))
        
        shap.summary_plot(
            self.shap_values_numpy[..., class_idx],
            self.X_train,
            feature_names=self.X_train.columns,
            plot_type="dot",
            show=False
            # cmap=cmap  # Using default colormap
        )
        
        # Customize Color Bar
        cbar = plt.gcf().axes[-1]
        cbar.set_ylabel('Parameter Value', fontsize=24)
        cbar.tick_params(labelsize=20)
        
        plt.title(f'SHAP Beeswarm Plot - Class F{class_idx}', fontsize=28, pad=20)
        
        if save:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f'SHAP_beeswarm_F{class_idx}.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Beeswarm plot saved to {filepath}")
        
        plt.close()
    
    def plot_interaction(
        self,
        class_idx: int = 0,
        max_display: int = 6,
        output_dir: str = 'outputs',
        save: bool = True
    ):
        """
        Plot interaction effects between features.
        
        Args:
            class_idx: Target class index.
            max_display: Maximum number of features to display.
            output_dir: Directory to save the plot.
            save: If True, saves the plot.
            cmap: Colormap for the plot.
        """
        print(f"Calculating SHAP interaction values for class F{class_idx} (this may take a while)...")
        shap_interaction_values = self.explainer_tree.shap_interaction_values(self.X_test)
        
        plt.figure(figsize=(14, 10))
        
        shap.summary_plot(
            shap_interaction_values[..., class_idx],
            self.X_test,
            show=False,
            max_display=max_display
            # cmap=cmap  # Using default colormap
        )
        
        # Clean up subplots
        axes = plt.gcf().axes
        for ax in axes:
            ax.spines['bottom'].set_linewidth(2)
            ax.tick_params(axis="x", labelsize=18, width=2)
            ax.set_title(ax.get_title(), fontsize=18)
        
        plt.suptitle(f'SHAP Interaction Plot - Class F{class_idx}', fontsize=28, y=0.995)
        plt.subplots_adjust(wspace=0.3, hspace=0.4)
        
        if save:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f'SHAP_interaction_F{class_idx}.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Interaction plot saved to {filepath}")
        
        plt.close()
    
    def plot_dependence(
        self,
        feature_x: str,
        feature_y: Optional[str] = None,
        class_idx: int = 0,
        output_dir: str = 'outputs',
        save: bool = True
    ):
        """
        Plot dependence plot showing feature relationship.
        Supports both single-variable and bivariate (dual-variable) plots.
        
        Args:
            feature_x: Main feature to analyze (X-axis).
            feature_y: Interaction feature for coloring (optional, auto-selected if None).
                      When provided, creates a bivariate plot showing the relationship
                      between feature_x's value and its SHAP value, colored by feature_y.
            class_idx: Target class index.
            output_dir: Directory to save the plot.
            save: If True, saves the plot.
        
        Returns:
            None
        
        Example:
            # Single-variable plot (auto-select interaction feature)
            plot_dependence('P1', class_idx=0)
            
            # Bivariate plot (explicit interaction feature)
            plot_dependence('P1', feature_y='P2', class_idx=0)
        """
        plt.figure(figsize=(12, 8))
        
        shap.dependence_plot(
            feature_x,
            self.shap_values_numpy[..., class_idx],
            self.X_train,
            interaction_index=feature_y,
            dot_size=120,
            show=False
        )
        
        # Customize Axes
        ax = plt.gca()
        ax.tick_params(axis='both', which='major', labelsize=22, width=2)
        ax.set_ylabel(f'SHAP value for {feature_x}', fontsize=26)
        ax.set_xlabel(f'{feature_x}', fontsize=26)
        ax.spines['bottom'].set_linewidth(3)
        ax.spines['left'].set_linewidth(3)
        
        # Title indicates whether it's univariate or bivariate
        if feature_y:
            plot_type = f"Bivariate Dependence"
            title = f'SHAP {plot_type} - Class F{class_idx}\n{feature_x} vs {feature_y}'
        else:
            plot_type = f"Univariate Dependence"
            title = f'SHAP {plot_type} - Class F{class_idx}\n{feature_x}'
        
        plt.title(title, fontsize=24, pad=20, fontweight='bold')
        
        if save:
            os.makedirs(output_dir, exist_ok=True)
            if feature_y:
                # Bivariate filename
                filepath = os.path.join(output_dir, f'SHAP_dependence_bivariate_F{class_idx}_{feature_x}_vs_{feature_y}.png')
            else:
                # Univariate filename
                filepath = os.path.join(output_dir, f'SHAP_dependence_F{class_idx}_{feature_x}.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Dependence plot saved to {filepath}")
        
        plt.close()
    
    def plot_composite(
        self,
        class_idx: int = 0,
        output_dir: str = 'outputs',
        save: bool = True
    ):
        """
        Plot composite plot combining Beeswarm (bottom) and Bar (top) plots.
        
        Args:
            class_idx: Target class index.
            output_dir: Directory to save the plot.
            save: If True, saves the plot.
            cmap: Colormap for the plot.
        """
        fig, ax1 = plt.subplots(figsize=(12, 10))
        
        # 1. Main Beeswarm Plot
        shap.summary_plot(
            self.shap_values_numpy[..., class_idx],
            self.X_train,
            feature_names=self.X_train.columns,
            plot_type="dot",
            show=False,
            color_bar=True
            # cmap=cmap  # Using default colormap
        )
        
        # Customize Color Bar
        cbar = plt.gcf().axes[-1]
        cbar.set_ylabel('Parameter Value', fontsize=24)
        cbar.tick_params(labelsize=20)
        
        # Adjust layout
        plt.gca().set_position([0.2, 0.2, 0.65, 0.65])
        
        # 2. Feature Importance Bar Plot (Top Axis)
        ax2 = ax1.twiny()
        
        shap.summary_plot(
            self.shap_values_numpy[..., class_idx],
            self.X_train,
            plot_type="bar",
            show=False
        )
        
        # Align position
        plt.gca().set_position([0.2, 0.2, 0.65, 0.65])
        
        # Style the bars
        bars = ax2.patches
        for bar in bars:
            bar.set_color('#CCE5FB')
            bar.set_alpha(0.4)
        
        # Customize Axes
        ax1.set_xlabel(f'Shapley Value Contribution (F{class_idx})', fontsize=24, labelpad=5)
        ax1.set_ylabel('Parameters', fontsize=24)
        ax2.set_xlabel('Mean Shapley Value (Parameter Importance)', fontsize=24, labelpad=10)
        
        # Position axes
        ax2.xaxis.set_label_position('top')
        ax2.xaxis.tick_top()
        
        # Layering
        ax1.set_zorder(ax1.get_zorder() + 1)
        ax1.patch.set_visible(False)
        
        plt.suptitle(f'SHAP Composite Analysis - Class F{class_idx}', fontsize=28, y=0.98)
        
        if save:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, f'SHAP_composite_F{class_idx}.png')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Composite plot saved to {filepath}")
        
        plt.close()
    
    def generate_all_plots(
        self,
        class_indices: Optional[List[int]] = None,
        output_dir: str = 'outputs',
        sample_idx: int = 0
    ):
        """
        Generate all SHAP plots for specified classes.
        
        Args:
            class_indices: List of class indices to analyze. If None, analyzes all classes.
            output_dir: Directory to save plots.
            sample_idx: Sample index for waterfall plot.
        """
        if class_indices is None:
            # Determine number of classes
            if len(self.shap_values_numpy.shape) == 3:
                n_classes = self.shap_values_numpy.shape[2]
            else:
                n_classes = 1
            class_indices = list(range(n_classes))
        
        print(f"\n{'='*70}")
        print(f"  Generating SHAP Analysis Plots")
        print(f"{'='*70}\n")
        
        for class_idx in class_indices:
            print(f"\nAnalyzing Class F{class_idx}...")
            
            # Waterfall plot
            self.plot_waterfall(class_idx=class_idx, sample_idx=sample_idx, 
                              output_dir=output_dir)
            
            # Beeswarm plot
            self.plot_beeswarm(class_idx=class_idx, output_dir=output_dir)
            
            # Composite plot
            self.plot_composite(class_idx=class_idx, output_dir=output_dir)
            
            # Dependence plot for top features
            feature_importance = np.abs(self.shap_values_numpy[..., class_idx]).mean(0)
            top_features_idx = np.argsort(feature_importance)[-2:][::-1]
            
            for feat_idx in top_features_idx[:1]:  # Plot top 1 feature
                feature_name = self.X_train.columns[feat_idx]
                self.plot_dependence(feature_name, class_idx=class_idx, 
                                   output_dir=output_dir)
        
        # Generate interaction plot for one representative class
        if len(class_indices) > 0:
            representative_class = class_indices[len(class_indices)//2]
            print(f"\nGenerating interaction plot for representative class F{representative_class}...")
            self.plot_interaction(class_idx=representative_class, output_dir=output_dir)
        
        print(f"\n{'='*70}")
        print(f"  SHAP Analysis Complete")
        print(f"{'='*70}\n")
