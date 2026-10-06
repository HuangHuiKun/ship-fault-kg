#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive SHAP Analysis Tool

Features:
1. User selects fault types to analyze (single or multiple)
2. User selects samples to analyze
3. Generates all types of SHAP charts:
   - Waterfall plot (single sample explanation)
   - Beeswarm plot (global feature importance)
   - Summary Plot (feature distribution)
   - Composite plot (combined view)
   - Dependence plot (single variable)
   - Dependence plot (bivariate ⭐)
   - Interaction plot (feature interaction)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_loader import load_data, prepare_data, get_class_names
from src.models import RandomForestModel
from src.shap_analysis import SHAPAnalyzer
import numpy as np
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

# Fault type names
FAULT_TYPES = {
    0: "Normal",
    1: "Head-crack",
    2: "Linner-wear",
    3: "Piston-ablation",
    4: "Ring-wear",
    5: "Ring-adhesion"
}

def print_separator(char='=', length=70):
    """Print separator line"""
    print(char * length)

def display_menu():
    """Display main menu"""
    print_separator()
    print("🔬 Interactive SHAP Analysis Tool")
    print_separator()
    print("\nAvailable fault types:")
    for idx, name in FAULT_TYPES.items():
        print(f"  [{idx}] {name}")
    print()

def get_user_choice(prompt, valid_choices):
    """Get user choice"""
    while True:
        try:
            choice = input(prompt)
            if choice.lower() == 'q':
                print("Exiting program")
                sys.exit(0)
            
            # Handle multiple choices (comma separated)
            if ',' in choice:
                choices = [int(x.strip()) for x in choice.split(',')]
                if all(c in valid_choices for c in choices):
                    return choices
                else:
                    print(f"❌ Invalid choice. Please enter values from {valid_choices}")
            else:
                choice_int = int(choice)
                if choice_int in valid_choices:
                    return [choice_int]
                else:
                    print(f"❌ Invalid choice. Please enter values from {valid_choices}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nExiting program")
            sys.exit(0)

def select_plot_types():
    """Select chart types to generate"""
    print("\nSelect SHAP chart types to generate:")
    print("  [1] Waterfall - Single sample prediction explanation")
    print("  [2] Beeswarm - Global feature importance distribution")
    print("  [3] Composite - Combined view (importance + distribution)")
    print("  [4] Dependence (bivariate) ⭐ - Feature interaction effects")
    print("  [5] Interaction - Feature interaction strength ranking")
    print("  [0] Generate all charts")
    
    choice = input("\nEnter selection (multiple separated by commas, e.g. '1,2,4') [default 0-all]: ").strip()
    
    if not choice or choice == '0':
        return [1, 2, 3, 4, 5]
    
    try:
        choices = [int(x.strip()) for x in choice.split(',')]
        return [c for c in choices if 1 <= c <= 5]
    except:
        return [1, 2, 3, 4, 5]

def main():
    display_menu()
    
    # 1. Select fault types
    print("━" * 70)
    print("Step 1: Select fault types to analyze")
    print("━" * 70)
    fault_indices = get_user_choice(
        "Enter fault type number (multiple separated by commas, e.g. '0,2,4') [default 0]: ",
        list(FAULT_TYPES.keys())
    )
    if not fault_indices:
        fault_indices = [0]
    
    print(f"\n✓ Selected: {[FAULT_TYPES[i] for i in fault_indices]}")
    
    # 2. Select chart types
    print("\n━" * 70)
    print("Step 2: Select SHAP chart types")
    print("━" * 70)
    plot_types = select_plot_types()
    
    plot_names = {
        1: "Waterfall", 2: "Beeswarm", 3: "Composite",
        4: "Dependence(univariate)", 5: "Dependence(bivariate)", 6: "Interaction"
    }
    print(f"\n✓ Selected: {[plot_names[p] for p in plot_types]}")
    
    # 3. Load and prepare data
    print("\n" + "=" * 70)
    print("Data Loading and Model Training")
    print("=" * 70)
    
    use_feature_selection = input("\nUse feature selection? [y/N]: ").strip().lower() == 'y'
    random_state = 20
    
    print("\n📊 Loading data...")
    X, y, label_encoder, _ = load_data(DATA_DIR, use_feature_selection=use_feature_selection)
    print(f"   ✓ Data shape: {X.shape}")
    print(f"   ✓ Number of features: {X.shape[1]}")
    if hasattr(X, 'columns'):
        print(f"   ✓ Feature names: {list(X.columns)}")
    
    print("\n📊 Preparing data...")
    X_train, X_test, y_train, y_test, scaler = prepare_data(
        X, y, test_size=216, random_state=random_state, normalize=True
    )
    print(f"   ✓ Training set: {X_train.shape}")
    print(f"   ✓ Test set: {X_test.shape}")
    
    # 4. Train model
    print("\n🤖 Training Random Forest model...")
    rf = RandomForestModel(n_estimators=20, random_state=random_state)
    rf.train(X_train, y_train)
    
    class_names = get_class_names(label_encoder)
    accuracy = rf.evaluate(X_test, y_test, class_names)['accuracy']
    print(f"   ✓ Model accuracy: {accuracy*100:.2f}%")
    
    # 5. Initialize SHAP analyzer
    print("\n⚙️  Initializing SHAP analyzer...")
    feature_names = list(X.columns) if hasattr(X, 'columns') else None
    shap_analyzer = SHAPAnalyzer(
        model=rf.model,
        X_train=X_train,
        X_test=X_test,
        feature_names=feature_names
    )
    print("   ✓ SHAP values computed")
    
    # Get sample count for each class in test set
    print("\n📊 Sample count per class in test set:")
    for class_idx in fault_indices:
        count = np.sum(y_test == class_idx)
        print(f"   {FAULT_TYPES[class_idx]}: {count} samples")
    
    # 6. Generate SHAP charts
    print("\n" + "=" * 70)
    print("Generating SHAP Visualization Charts")
    print("=" * 70)
    
    for class_idx in fault_indices:
        print(f"\n{'━' * 70}")
        print(f"Analyzing: {FAULT_TYPES[class_idx]}")
        print(f"{'━' * 70}")
        
        # Waterfall plot
        if 1 in plot_types:
            # Find test samples of this class
            class_samples = np.where(y_test == class_idx)[0]
            if len(class_samples) > 0:
                print(f"\nThis class has {len(class_samples)} test samples")
                sample_choice = input(f"Select sample index [0-{len(class_samples)-1}, default 0]: ").strip()
                sample_idx = int(sample_choice) if sample_choice.isdigit() else 0
                sample_idx = min(sample_idx, len(class_samples)-1)
                
                actual_sample_idx = class_samples[sample_idx]
                print(f"\n📊 Generating Waterfall plot (sample #{actual_sample_idx})...")
                shap_analyzer.plot_waterfall(
                    class_idx=class_idx,
                    sample_idx=actual_sample_idx,
                    output_dir=OUTPUT_DIR
                )
                print(f"   ✓ SHAP_waterfall_F{class_idx}_sample{actual_sample_idx}.png")
            else:
                print(f"   ⚠️  No samples of class {class_idx} in test set, skipping Waterfall plot")
        
        # Beeswarm plot
        if 2 in plot_types:
            print(f"\n📊 Generating Beeswarm plot...")
            shap_analyzer.plot_beeswarm(
                class_idx=class_idx,
                output_dir=OUTPUT_DIR
            )
            print(f"   ✓ SHAP_beeswarm_F{class_idx}.png")
        
        # Composite plot
        if 3 in plot_types:
            print(f"\n📊 Generating Composite plot...")
            shap_analyzer.plot_composite(
                class_idx=class_idx,
                output_dir=OUTPUT_DIR
            )
            print(f"   ✓ SHAP_composite_F{class_idx}.png")
        
        # Bivariate Dependence plot ⭐
        if 4 in plot_types:
            print(f"\n⭐ Generating bivariate Dependence plot (feature interaction effects)...")
            
            # Display all features with their numbers
            all_features = list(X.columns) if hasattr(X, 'columns') else [f'Feature_{i}' for i in range(X.shape[1])]
            print("\nAvailable feature numbers:")
            for i, feat_name in enumerate(all_features):
                print(f"  P{i+1:02d}: {feat_name}")
            
            # Get top features for recommendation
            feature_importance = np.abs(shap_analyzer.shap_values_numpy[..., class_idx]).mean(0)
            top_features_idx = np.argsort(feature_importance)[-4:][::-1]
            top_features_nums = [f"P{i+1:02d}" for i in top_features_idx]
            top_features_names = [all_features[i] for i in top_features_idx]
            
            print(f"\n💡 Recommended (Top-4 important features):")
            for num, name in zip(top_features_nums, top_features_names):
                print(f"  {num}: {name}")
            
            # Manually specify feature pairs (using numbers)
            print("\nEnter feature pairs (using numbers P01-P14):")
            print("Example: P01-P02,P03-P04  or  P01-P05")
            pairs_input = input("Feature pairs (multiple separated by commas): ").strip()
            
            if pairs_input:
                pairs = [pair.strip().split('-') for pair in pairs_input.split(',')]
                print("\nStarting generation...")
                for feat_x_num, feat_y_num in pairs:
                    feat_x_num = feat_x_num.strip().upper()
                    feat_y_num = feat_y_num.strip().upper()
                    
                    try:
                        # Parse number (P01 -> 0, P02 -> 1, ...)
                        if feat_x_num.startswith('P') and feat_y_num.startswith('P'):
                            x_idx = int(feat_x_num[1:]) - 1
                            y_idx = int(feat_y_num[1:]) - 1
                            
                            if 0 <= x_idx < len(all_features) and 0 <= y_idx < len(all_features):
                                feat_x = all_features[x_idx]
                                feat_y = all_features[y_idx]
                                
                                shap_analyzer.plot_dependence(
                                    feature_x=feat_x,
                                    feature_y=feat_y,
                                    class_idx=class_idx,
                                    output_dir=OUTPUT_DIR
                                )
                                print(f"   ✓ {feat_x_num}({feat_x}) vs {feat_y_num}({feat_y})")
                            else:
                                print(f"   ✗ {feat_x_num}-{feat_y_num} - Number out of range (P01-P{len(all_features):02d})")
                        else:
                            print(f"   ✗ {feat_x_num}-{feat_y_num} - Format error (should be P01-P14 format)")
                    except ValueError:
                        print(f"   ✗ {feat_x_num}-{feat_y_num} - Number format error")
                    except Exception as e:
                        print(f"   ✗ {feat_x_num}-{feat_y_num} - Error: {str(e)}")
            else:
                print("   ⚠️  No feature pairs entered, skipping bivariate plot generation")
    
    # Interaction plot (generate only once)
    if 5 in plot_types:
        representative_class = fault_indices[len(fault_indices)//2]
        print(f"\n{'━' * 70}")
        print(f"📊 Generating Interaction plot (representative class: {FAULT_TYPES[representative_class]})...")
        print(f"{'━' * 70}")
        shap_analyzer.plot_interaction(
            class_idx=representative_class,
            output_dir=OUTPUT_DIR
        )
        print(f"   ✓ SHAP_interaction_F{representative_class}.png")
    
    # 7. Summary
    print("\n" + "=" * 70)
    print("✅ SHAP Analysis Complete!")
    print("=" * 70)
    print(f"\n📁 All charts saved to: {OUTPUT_DIR}/")
    
    # Display generated files
    import glob
    shap_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, 'SHAP_*.png')))
    print(f"\nGenerated {len(shap_files)} SHAP charts:")
    for f in shap_files[-20:]:  # Show last 20
        print(f"  ✓ {os.path.basename(f)}")
    
    if len(shap_files) > 20:
        print(f"  ... and {len(shap_files)-20} more files")
    
    print("\n💡 Tips:")
    print("  - Bivariate plot filenames contain 'bivariate' keyword")
    print("  - Color represents the second feature's value, observe color patterns to identify interaction effects")
    print("  - For more information, see SHAP_BIVARIATE_GUIDE.py")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
        sys.exit(0)
