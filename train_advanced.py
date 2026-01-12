
import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import json
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin

# --- CONFIGURATION ---
DATA_PATH = "recs2020_public_v7.csv"
MODEL_DIR = "models_advanced"
os.makedirs(MODEL_DIR, exist_ok=True)

# Define Base Features (Global Scope)
NUMERIC_FEATURES = [
    'TOTSQFT_EN', # Total conditioned sqft
    'HDD65',      # Heating Degree Days
    'CDD65',      # Cooling Degree Days
    'NHSLDMEM',   # Household Members
    'NUMFRIG',    # Number of fridges
    'NUMFREEZ',   # Number of freezers
    'TVCOLOR',    # Number of TVs
    'NUMLAPTOP',  # Laptops
    'NUMTABLET',  # Tablets
    'NUMSMPHONE'  # Smartphones
]

CATEGORICAL_FEATURES = [
    'DIVISION',      # Region
    'TYPEHUQ',       # Housing Unit Type
    'UATYP10',       # Urban/Rural
    'YEARMADERANGE', # Year Built
    'WALLTYPE',      # Wall Material
    'ROOFTYPE',      # Roof
    'WINDOWS',       # Windows Frequency
    'ADQINSUL',      # Insulation Quality
    'DRAFTY',        # Draftiness
    'EQUIPM',        # Main Heating Equipment
    'FUELHEAT',      # Main Heating Fuel
    'ACEQUIPM_PUB',  # Cooling Type
    'WHEATSIZ',      # Water Heater Size
    'FUELH2O',       # Water Heater Fuel
    'WHEATBKT',      # Tankless indicator
    'AGECWASH',      # Age of Washer
    'AGEDW',         # Age of Dishwasher
    'AGERFRI1',      # Age of Main Fridge
    'LGTINLED',      # LED Lighting Portion
    'SMARTMETER',    # Smart Meter
    'SDESCENT',      # Householder Descent
    'EDUCATION',     # Education
    'EMPLOYHH',      # Employment
    'PAYHELP',       # Energy Insecurity
    'NOHEATBROKE'    # Energy Insecurity
]

TARGETS = {
    'total_kbtu': 'TOTALBTU',
    'heating_kbtu': 'TOTALBTUSPH',
    'cooling_kbtu': 'BTUELCOL',
    'water_kbtu': 'TOTALBTUWTH',
    'baseload_kbtu': 'BTUELNEC'
}

def load_data(filepath):
    print(f"Loading {filepath}...")
    df = pd.read_csv(filepath, low_memory=False)
    
    # Feature Engineering: Interactions
    print("Generating Interaction Features...")
    
    # 1. Heating Intensity: HDD * SqFt
    df['HDD_x_SQFT'] = df['HDD65'] * df['TOTSQFT_EN']
    
    # 2. Cooling Intensity: CDD * SqFt
    df['CDD_x_SQFT'] = df['CDD65'] * df['TOTSQFT_EN']
    
    # 3. Usage Intensity: SqFt Per Person
    # Handle division by zero
    members = df['NHSLDMEM'].replace(0, 1)
    df['SQFT_PER_CAPITA'] = df['TOTSQFT_EN'] / members
    
    return df

def train_and_optimize():
    df = load_data(DATA_PATH)
    
    # Extended Numeric Features list (including engineered ones)
    EXT_NUMERIC_FEATURES = NUMERIC_FEATURES + ['HDD_x_SQFT', 'CDD_x_SQFT', 'SQFT_PER_CAPITA']
    
    # Define ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), EXT_NUMERIC_FEATURES),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES)
        ]
    )
    
    # Prepare X (Features)
    feature_cols = EXT_NUMERIC_FEATURES + CATEGORICAL_FEATURES
    
    # Check for missing columns in CSV and fill defaults
    for col in feature_cols:
        if col not in df.columns:
            print(f"Warning: Missing column {col}, filling with defaults.")
            df[col] = 0 if col in EXT_NUMERIC_FEATURES else "Unknown"
    
    # Drop rows where Targets are NaN (only relevant for supervised training)
    # Actually, keep all and split per target loop
    
    X = df[feature_cols]
    
    # Save Metadata for API to know what to expect
    meta = {
        'numeric': EXT_NUMERIC_FEATURES, # API must compute interactions before passing to model? 
                                         # No, typically API receives raw inputs and computes interactions internally. 
                                         # Wait, main.py needs to know to compute these! 
                                         # We should update main.py to compute these if the model expects them.
                                         # For now, let's assume API computes them.
        'categorical': CATEGORICAL_FEATURES
    }
    with open(f"{MODEL_DIR}/feature_meta.pkl", "wb") as f:
        pickle.dump(meta, f)
        
    print("Fitting Global Preprocessor...")
    # Handle NaN in X for fitting
    X = X.fillna(0) # Simple imputation for numeric, "Unknown" for cat handled above?
    # Actually OneHotEncoder fails on NaN if not string.
    for c in CATEGORICAL_FEATURES:
        X[c] = X[c].astype(str)
        
    X_processed = preprocessor.fit_transform(X)
    
    # Save Preprocessor
    with open(f"{MODEL_DIR}/preprocessor.pkl", "wb") as f:
        pickle.dump(preprocessor, f)
        
    results = {}
    
    # --- HYPERPARAMETER TUNING CONFIGURATION ---
    # Senior Engineer Note: Reduced grid for speed in this demo, but scalable.
    param_grid = {
        'n_estimators': [200, 300],
        'max_depth': [5, 7],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8],
        'colsample_bytree': [0.8]
    }
    
    for name, target_col in TARGETS.items():
        print(f"\nTraining Model: {name} ({target_col})...")
        
        # Filter valid target rows
        mask = df[target_col].notna() & (df[target_col] >= 0)
        y = df.loc[mask, target_col]
        X_subset = X_processed[mask]
        
        if len(y) < 100:
            print("Not enough data. Skipping.")
            continue
            
        # Split
        X_train, X_test, y_train, y_test = train_test_split(X_subset, y, test_size=0.2, random_state=42)
        
        print(f" > Training samples: {len(X_train)}")
        
        # Grid Search
        # Using a smaller n_estimators for grid search speed, then could retrain larger.
        xgb_model = xgb.XGBRegressor(objective='reg:squarederror', n_jobs=-1, random_state=42)
        
        grid = GridSearchCV(
            estimator=xgb_model,
            param_grid=param_grid,
            cv=3,
            scoring='neg_mean_absolute_error',
            verbose=1,
            n_jobs=-1 # Parallel
        )
        
        grid.fit(X_train, y_train)
        
        best_model = grid.best_estimator_
        best_mae = -grid.best_score_
        print(f" > Best Params: {grid.best_params_}")
        print(f" > Best CV MAE: {best_mae:.2f}")
        
        # Test Set Validation
        preds = best_model.predict(X_test)
        test_r2 = r2_score(y_test, preds)
        test_mae = mean_absolute_error(y_test, preds)
        
        print(f"  > Test R2: {test_r2:.4f}")
        print(f"  > Test MAE: {test_mae:.2f}")
        
        results[name] = {
            'r2': test_r2, 
            'mae': test_mae, 
            'best_params': grid.best_params_
        }
        
        # Save Artifact
        with open(f"{MODEL_DIR}/xgb_{name}.pkl", "wb") as f:
            pickle.dump(best_model, f)
            
    print("\n--- Final Optimization Results ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    train_and_optimize()
