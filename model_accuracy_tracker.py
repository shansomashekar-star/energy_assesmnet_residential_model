"""
Model Accuracy Tracker
----------------------
Tracks model performance, feature importance, and prediction accuracy.
Provides detailed analytics for model improvement.
"""

import pickle
import json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


class ModelAccuracyTracker:
    """Tracks and reports model accuracy metrics."""
    
    def __init__(self, model_dir="models_advanced"):
        self.model_dir = model_dir
        self.metrics = {}
    
    def evaluate_model(self, model_name, y_true, y_pred):
        """Calculate comprehensive accuracy metrics."""
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        
        # Remove any invalid values
        mask = np.isfinite(y_true) & np.isfinite(y_pred) & (y_true >= 0) & (y_pred >= 0)
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        if len(y_true) == 0:
            return None
        
        metrics = {
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'r2': float(r2_score(y_true, y_pred)),
            'mean_actual': float(np.mean(y_true)),
            'mean_predicted': float(np.mean(y_pred)),
            'median_actual': float(np.median(y_true)),
            'median_predicted': float(np.median(y_pred)),
            'samples': int(len(y_true))
        }
        
        # Percentage errors
        metrics['mae_percent'] = (metrics['mae'] / metrics['mean_actual'] * 100) if metrics['mean_actual'] > 0 else 0
        metrics['rmse_percent'] = (metrics['rmse'] / metrics['mean_actual'] * 100) if metrics['mean_actual'] > 0 else 0
        
        # Accuracy within 10%, 15%, 20%
        errors = np.abs(y_true - y_pred) / y_true * 100
        metrics['accuracy_10pct'] = float(np.mean(errors <= 10))
        metrics['accuracy_15pct'] = float(np.mean(errors <= 15))
        metrics['accuracy_20pct'] = float(np.mean(errors <= 20))
        
        return metrics
    
    def get_feature_importance(self, model_name):
        """Extract feature importance from trained model."""
        try:
            with open(f"{self.model_dir}/xgb_{model_name}.pkl", "rb") as f:
                model = pickle.load(f)
            
            if hasattr(model, 'feature_importances_'):
                # Get feature names from metadata
                with open(f"{self.model_dir}/feature_meta.pkl", "rb") as f:
                    meta = pickle.load(f)
                
                # Combine numeric and categorical feature names
                # Note: OneHotEncoder creates multiple features from categorical
                numeric_features = meta.get('numeric', [])
                categorical_features = meta.get('categorical', [])
                
                # For now, return importance scores
                importances = model.feature_importances_
                
                return {
                    'total_features': len(importances),
                    'top_10_importance': float(np.sum(np.sort(importances)[-10:])),
                    'top_20_importance': float(np.sum(np.sort(importances)[-20:])),
                    'max_importance': float(np.max(importances)),
                    'mean_importance': float(np.mean(importances))
                }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_accuracy_report(self, test_results):
        """Generate comprehensive accuracy report."""
        report = {
            'summary': {},
            'models': {},
            'overall_accuracy': {}
        }
        
        # Aggregate metrics
        all_mae = []
        all_r2 = []
        all_accuracy_15pct = []
        
        for model_name, metrics in test_results.items():
            if metrics:
                report['models'][model_name] = metrics
                all_mae.append(metrics['mae_percent'])
                all_r2.append(metrics['r2'])
                all_accuracy_15pct.append(metrics['accuracy_15pct'])
        
        if all_mae:
            report['summary'] = {
                'average_mae_percent': float(np.mean(all_mae)),
                'average_r2': float(np.mean(all_r2)),
                'average_accuracy_15pct': float(np.mean(all_accuracy_15pct)),
                'models_tested': len(all_mae)
            }
            
            report['overall_accuracy'] = {
                'excellent': report['summary']['average_mae_percent'] < 10,
                'good': report['summary']['average_mae_percent'] < 15,
                'acceptable': report['summary']['average_mae_percent'] < 20,
                'needs_improvement': report['summary']['average_mae_percent'] >= 20
            }
        
        return report
    
    def save_report(self, report, filename="model_accuracy_report.json"):
        """Save accuracy report to file."""
        with open(f"{self.model_dir}/{filename}", "w") as f:
            json.dump(report, f, indent=2)
        print(f"Accuracy report saved to {self.model_dir}/{filename}")


def validate_predictions(actual, predicted, tolerance_percent=15):
    """
    Validate predictions against actual values.
    
    Returns:
        dict with validation results
    """
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    # Calculate errors
    errors = np.abs(actual - predicted)
    percent_errors = (errors / actual * 100) if np.any(actual > 0) else errors
    
    validation = {
        'within_tolerance': float(np.mean(percent_errors <= tolerance_percent)),
        'mean_error_percent': float(np.mean(percent_errors)),
        'max_error_percent': float(np.max(percent_errors)),
        'min_error_percent': float(np.min(percent_errors)),
        'std_error_percent': float(np.std(percent_errors))
    }
    
    return validation
