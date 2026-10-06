"""
Machine Learning Models module for engine health state classification.

This module provides wrapper classes for KNN, Random Forest, and SVM classifiers
with hyperparameter tuning capabilities.
"""

from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
import numpy as np
from typing import Dict, Tuple, Optional
import pandas as pd


class BaseClassifier:
    """Base class for all classifiers."""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.model = None
        self.best_params = None
        
    def train(self, X_train, y_train):
        """Train the model."""
        self.model.fit(X_train, y_train)
        return self
    
    def predict(self, X_test):
        """Make predictions."""
        return self.model.predict(X_test)
    
    def predict_proba(self, X_test):
        """Get prediction probabilities."""
        return self.model.predict_proba(X_test)
    
    def evaluate(self, X_test, y_test, class_names: list) -> Dict:
        """
        Evaluate the model and return metrics.
        
        Args:
            X_test: Test features.
            y_test: True labels.
            class_names: List of class names.
        
        Returns:
            Dictionary containing evaluation metrics.
        """
        y_pred = self.predict(X_test)
        y_pred_prob = self.predict_proba(X_test)
        
        # Calculate accuracy
        accuracy = accuracy_score(y_test, y_pred)
        
        # Generate classification report
        report = classification_report(
            y_test, y_pred,
            target_names=class_names,
            output_dict=True
        )
        
        # Calculate AUC for each class
        n_classes = len(class_names)
        auc_scores = {}
        for i in range(n_classes):
            auc = roc_auc_score(y_test == i, y_pred_prob[:, i])
            auc_scores[class_names[i]] = auc
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'auc_scores': auc_scores,
            'y_pred': y_pred,
            'y_pred_prob': y_pred_prob
        }


class KNNClassifier(BaseClassifier):
    """K-Nearest Neighbors Classifier with Grid Search."""
    
    def __init__(self, random_state: int = 42, n_splits: int = 10):
        super().__init__(random_state)
        self.n_splits = n_splits
        self.param_grid = {
            'n_neighbors': [3, 5, 7, 9, 11, 13, 15],
            'weights': ['uniform', 'distance'],
            'metric': ['euclidean', 'manhattan', 'minkowski', 'chebyshev']
        }
        
    def train(self, X_train, y_train, use_grid_search: bool = True):
        """
        Train KNN model with optional grid search.
        
        Args:
            X_train: Training features.
            y_train: Training labels.
            use_grid_search: If True, performs hyperparameter tuning.
        
        Returns:
            self
        """
        if use_grid_search:
            cv = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
            knn = KNeighborsClassifier()
            grid_search = GridSearchCV(knn, self.param_grid, cv=cv, scoring='accuracy', n_jobs=-1)
            grid_search.fit(X_train, y_train)
            
            self.best_params = grid_search.best_params_
            self.model = grid_search.best_estimator_
            print(f"[KNN] Best Parameters: {self.best_params}")
            print(f"[KNN] Best CV Score: {grid_search.best_score_:.4f}")
        else:
            self.model = KNeighborsClassifier(n_neighbors=5)
            self.model.fit(X_train, y_train)
        
        return self


class RandomForestModel(BaseClassifier):
    """Random Forest Classifier."""
    
    def __init__(self, n_estimators: int = 20, random_state: int = 42):
        super().__init__(random_state)
        self.n_estimators = n_estimators
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state
        )
    
    def train(self, X_train, y_train):
        """Train Random Forest model."""
        self.model.fit(X_train, y_train)
        print(f"[RF] n_estimators: {self.n_estimators}")
        return self
    
    def get_feature_importance(self, feature_names: list) -> pd.DataFrame:
        """Get feature importance scores."""
        importance = self.model.feature_importances_
        return pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)


class SVMClassifier(BaseClassifier):
    """Support Vector Machine Classifier."""
    
    def __init__(self, kernel: str = 'linear', random_state: int = 42):
        super().__init__(random_state)
        self.kernel = kernel
        self.model = SVC(
            kernel=kernel,
            random_state=random_state,
            probability=True
        )
    
    def train(self, X_train, y_train):
        """Train SVM model."""
        self.model.fit(X_train, y_train)
        print(f"[SVM] Kernel: {self.kernel}")
        return self


def compare_models(models_results: Dict) -> pd.DataFrame:
    """
    Compare multiple models based on their evaluation metrics.
    
    Args:
        models_results: Dictionary with model names as keys and evaluation results as values.
    
    Returns:
        DataFrame with comparison metrics.
    """
    comparison = []
    
    for model_name, results in models_results.items():
        row = {
            'Model': model_name,
            'Accuracy': results['accuracy'],
            'Macro Avg F1': results['classification_report']['macro avg']['f1-score'],
            'Weighted Avg F1': results['classification_report']['weighted avg']['f1-score'],
        }
        
        # Add AUC scores
        for class_name, auc in results['auc_scores'].items():
            row[f'AUC_{class_name}'] = auc
        
        comparison.append(row)
    
    return pd.DataFrame(comparison)
