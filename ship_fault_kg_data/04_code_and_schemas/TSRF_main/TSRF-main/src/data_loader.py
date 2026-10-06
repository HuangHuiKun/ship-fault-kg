"""
Data loading and preprocessing module for engine health state classification.

This module provides functions to load and preprocess the engine sensor data
for multi-class classification of health states.
"""

import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, Optional


# Data file configuration
DATA_FILES = [
    'Normal.csv',
    'Head-crack.csv', 
    'Linner-wear.csv',
    'Piston-ablation.csv',
    'Ring-adhesion.csv',
    'Ring-wear.csv'
]

HEALTH_STATES = [
    'Normal',
    'Head-crack',
    'Linner-wear', 
    'Piston-ablation',
    'Ring-adhesion',
    'Ring-wear'
]

# Features to drop when using feature selection
FEATURES_TO_DROP = [
    'Cylinder-Pre',
    'TurbinePower',
    'Out-Pre',
    'Out-Tem',
    'Turbine-out-Pre'
]


def load_data(data_dir: str, use_feature_selection: bool = False) -> Tuple[pd.DataFrame, pd.Series, LabelEncoder, Dict]:
    """
    Load and preprocess engine health state data.
    
    Args:
        data_dir: Path to the directory containing the CSV data files.
        use_feature_selection: If True, drops certain features for dimensionality reduction.
    
    Returns:
        X: Feature DataFrame.
        y: Target Series with encoded labels.
        label_encoder: Fitted LabelEncoder for target labels.
        feature_mapping: Dictionary mapping original feature names to numbered names (P1, P2, ...).
    """
    data_list = []
    
    # Load all data files
    for file_name, state in zip(DATA_FILES, HEALTH_STATES):
        file_path = os.path.join(data_dir, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        data = pd.read_csv(file_path)
        data['Health_State'] = state
        data_list.append(data)
    
    # Concatenate all datasets
    df = pd.concat(data_list, ignore_index=True)
    
    # Drop 'Crank Angle' column if exists
    if 'Crank Angle' in df.columns:
        df = df.drop(columns=['Crank Angle'])
    
    # Apply feature selection if requested
    if use_feature_selection:
        cols_to_drop = [col for col in FEATURES_TO_DROP if col in df.columns]
        df = df.drop(columns=cols_to_drop)
    
    # Encode target labels
    label_encoder = LabelEncoder()
    df['Health_State'] = label_encoder.fit_transform(df['Health_State'])
    
    # Separate features and target
    X = df.drop(columns=['Health_State'])
    y = df['Health_State']
    
    # Create feature mapping
    feature_names = X.columns.tolist()
    feature_numbered_names = [f'P{i + 1}' for i in range(len(feature_names))]
    feature_mapping = dict(zip(feature_names, feature_numbered_names))
    
    return X, y, label_encoder, feature_mapping


def prepare_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: int = 216,
    random_state: int = 42,
    normalize: bool = True
) -> Tuple:
    """
    Prepare data for model training by splitting and optionally normalizing.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Number of samples for test set.
        random_state: Random seed for reproducibility.
        normalize: If True, applies StandardScaler normalization.
    
    Returns:
        X_train: Training features.
        X_test: Test features.
        y_train: Training labels.
        y_test: Test labels.
        scaler: Fitted StandardScaler (or None if normalize=False).
    """
    scaler = None
    X_processed = X.values if isinstance(X, pd.DataFrame) else X
    
    if normalize:
        scaler = StandardScaler()
        X_processed = scaler.fit_transform(X_processed)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y,
        test_size=test_size,
        stratify=y,
        random_state=random_state
    )
    
    return X_train, X_test, y_train, y_test, scaler


def get_class_names(label_encoder: LabelEncoder) -> list:
    """
    Generate class names in F0, F1, ... format.
    
    Args:
        label_encoder: Fitted LabelEncoder.
    
    Returns:
        List of class names.
    """
    n_classes = len(label_encoder.classes_)
    return [f'F{i}' for i in range(n_classes)]
