
import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

# Parameters
DATA_PATH = "recs2020_public_v7.csv"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def load_and_prep_data(filepath):
    """Loads RECS data and filters for relevant columns."""
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath, low_memory=False)
    
    # Filter for Single Family and Apartments mostly (TYPEHUQ)
    # 2 = Single Family, 5 = Apt in 5+ units
    # For simplicity, we keep all valid residential observations
    
    # Feature Selection
    # Inputs:
    # TOTSQFT_EN: Total Square Footage
    # HDD65: Heating Degree Days
    # CDD65: Cooling Degree Days
    # NHSLDMEM: Number of household members
    # YEARMADERANGE: Year built range (categorical, we need to encode)
    
    # Target:
    # TOTALBTU: Total Energy Consumption
    
    features = ['TOTSQFT_EN', 'HDD65', 'CDD65', 'NHSLDMEM', 'YEARMADERANGE']
    targets = ['TOTALBTU', 'KWHSPH', 'KWHCOL', 'KWHWTH', 'KWHRFG', 'KWHNEC']
    
    # Keep only rows with valid data
    df = df[features + targets].dropna()
    
    # Convert 'YEARMADERANGE' to numeric midpoint for simplicity or Keep as Ordinal
    # RECS ranges: 1=Before 1950, 2=1950-1959, ..., 8=2016-2020
    # We can treat it as ordinal integer 1-8.
    df['YEARMADERANGE'] = pd.to_numeric(df['YEARMADERANGE'], errors='coerce')
    
    return df

def train_benchmark_model(df):
    """Trains a KNN model to find similar peers."""
    print("Training Benchmark Model (KNN)...")
    
    feature_cols = ['TOTSQFT_EN', 'HDD65', 'CDD65', 'NHSLDMEM', 'YEARMADERANGE']
    X = df[feature_cols]
    
    # Scaling is crucial for KNN
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # K=50 for stable peer groups
    knn = NearestNeighbors(n_neighbors=50, algorithm='ball_tree')
    knn.fit(X_scaled)
    
    # Save artifacts
    with open(f"{MODEL_DIR}/benchmark_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(f"{MODEL_DIR}/benchmark_knn.pkl", "wb") as f:
        pickle.dump(knn, f)
    
    # Also save the reference dataset (subset) to look up percentiles
    # We only need the Target variable for the peers
    df[['TOTALBTU']].to_pickle(f"{MODEL_DIR}/benchmark_data.pkl")
    
    print("Benchmark Model Saved.")

def train_disaggregation_models(df):
    """Trains XGBoost models for end-use breakdown."""
    print("Training Disaggregation Models (XGBoost)...")
    
    X = df[['TOTSQFT_EN', 'HDD65', 'CDD65', 'NHSLDMEM', 'YEARMADERANGE']]
    
    # Targets (in kWh or kBtu equivalent)
    # We will train separate models for simplicity
    end_uses = {
        'heating_kwh': 'KWHSPH',
        'cooling_kwh': 'KWHCOL',
        'water_heat_kwh': 'KWHWTH',
        'baseload_kwh': 'KWHNEC' # Not Exactly Correct, NEC is "Not Elsewhere Classified", but serves as proxy for unique loads
    }
    
    for name, target_col in end_uses.items():
        print(f"  Training {name} model...")
        y = df[target_col]
        
        # Simple XGBoost Regressor
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, n_jobs=-1)
        model.fit(X, y)
        
        # Save
        with open(f"{MODEL_DIR}/model_{name}.pkl", "wb") as f:
            pickle.dump(model, f)

    print("Disaggregation Models Saved.")

def main():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found.")
        return

    df = load_and_prep_data(DATA_PATH)
    
    train_benchmark_model(df)
    train_disaggregation_models(df)
    
    print("Training Pipeline Complete!")

if __name__ == "__main__":
    main()
