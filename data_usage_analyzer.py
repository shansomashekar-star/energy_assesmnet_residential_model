"""
Data Usage Analyzer
-------------------
Tracks and reports how features are being used in predictions.
Helps identify which features are most important for accuracy.
"""

import pickle
import numpy as np
import pandas as pd
import json
from collections import defaultdict


class DataUsageAnalyzer:
    """Analyzes how data features are being used in the model."""
    
    def __init__(self, model_dir="models_advanced"):
        self.model_dir = model_dir
        self.usage_stats = defaultdict(int)
        self.feature_importance = {}
    
    def load_feature_importance(self):
        """Load feature importance from trained models."""
        try:
            with open(f"{self.model_dir}/feature_meta.pkl", "rb") as f:
                meta = pickle.load(f)
            
            importance_data = {}
            
            for model_name in ['total_kbtu', 'heating_kbtu', 'cooling_kbtu', 'water_kbtu', 'baseload_kbtu']:
                try:
                    with open(f"{self.model_dir}/xgb_{model_name}.pkl", "rb") as f:
                        model = pickle.load(f)
                    
                    if hasattr(model, 'feature_importances_'):
                        importances = model.feature_importances_
                        
                        # Get feature names
                        numeric_features = meta.get('numeric', [])
                        categorical_features = meta.get('categorical', [])
                        
                        # Note: OneHotEncoder expands categoricals, so we have more features
                        # For now, track overall importance distribution
                        importance_data[model_name] = {
                            'total_features': len(importances),
                            'max_importance': float(np.max(importances)),
                            'mean_importance': float(np.mean(importances)),
                            'std_importance': float(np.std(importances)),
                            'top_10_sum': float(np.sum(np.sort(importances)[-10:])),
                            'top_20_sum': float(np.sum(np.sort(importances)[-20:])),
                            'importance_distribution': {
                                'very_high': float(np.sum(importances > 0.05)),
                                'high': float(np.sum((importances > 0.01) & (importances <= 0.05))),
                                'medium': float(np.sum((importances > 0.001) & (importances <= 0.01))),
                                'low': float(np.sum(importances <= 0.001))
                            }
                        }
                except Exception as e:
                    importance_data[model_name] = {'error': str(e)}
            
            self.feature_importance = importance_data
            return importance_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_feature_usage(self, input_data):
        """Analyze which features are being used in a prediction."""
        usage = {
            'provided_features': [],
            'missing_features': [],
            'default_features': [],
            'feature_categories': {
                'building_envelope': 0,
                'hvac': 0,
                'appliances': 0,
                'water_heating': 0,
                'lighting': 0,
                'behavioral': 0,
                'climate': 0
            }
        }
        
        # Categorize features
        building_envelope = ['TOTSQFT_EN', 'STORIES', 'WALLTYPE', 'ROOFTYPE', 'WINDOWS', 
                            'TYPEGLASS', 'ADQINSUL', 'DRAFTY', 'ATTIC', 'CELLAR', 'CRAWL']
        hvac = ['EQUIPM', 'FUELHEAT', 'ACEQUIPM_PUB', 'ACEQUIPAGE', 'THERMAIN', 'PROTHERM',
               'TEMPHOME', 'TEMPGONE', 'TEMPNITE', 'DUCTS', 'DUCTINSUL']
        appliances = ['NUMFRIG', 'NUMFREEZ', 'AGERFRI1', 'RANGE', 'DISHWASH', 'CWASHER', 
                     'DRYER', 'TVCOLOR']
        water_heating = ['FUELH2O', 'WHEATSIZ', 'WHEATAGE', 'WHEATBKT']
        lighting = ['LGTINLED', 'LGTINCFL', 'LGTINCAN']
        behavioral = ['NHSLDMEM', 'ATHOME', 'EDUCATION', 'EMPLOYHH']
        climate = ['HDD65', 'CDD65', 'DIVISION']
        
        for key, value in input_data.items():
            if value is not None and value != '' and value != 0:
                usage['provided_features'].append(key)
                
                # Categorize
                if key in building_envelope:
                    usage['feature_categories']['building_envelope'] += 1
                elif key in hvac:
                    usage['feature_categories']['hvac'] += 1
                elif key in appliances:
                    usage['feature_categories']['appliances'] += 1
                elif key in water_heating:
                    usage['feature_categories']['water_heating'] += 1
                elif key in lighting:
                    usage['feature_categories']['lighting'] += 1
                elif key in behavioral:
                    usage['feature_categories']['behavioral'] += 1
                elif key in climate:
                    usage['feature_categories']['climate'] += 1
            else:
                usage['default_features'].append(key)
        
        return usage
    
    def generate_usage_report(self):
        """Generate comprehensive usage report."""
        report = {
            'feature_importance': self.feature_importance,
            'usage_statistics': dict(self.usage_stats),
            'recommendations': []
        }
        
        # Analyze importance data
        if self.feature_importance:
            for model_name, data in self.feature_importance.items():
                if 'error' not in data:
                    top_10_sum = data.get('top_10_sum', 0)
                    if top_10_sum < 0.5:
                        report['recommendations'].append(
                            f"{model_name}: Feature importance is spread out. Consider feature selection."
                        )
                    if data.get('mean_importance', 0) < 0.001:
                        report['recommendations'].append(
                            f"{model_name}: Many features have very low importance. Consider removing them."
                        )
        
        return report
    
    def save_report(self, filename="data_usage_report.json"):
        """Save usage report to file."""
        report = self.generate_usage_report()
        with open(f"{self.model_dir}/{filename}", "w") as f:
            json.dump(report, f, indent=2)
        print(f"Data usage report saved to {self.model_dir}/{filename}")
