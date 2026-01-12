
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Union
import pickle
import pandas as pd
import numpy as np
import os
from audit_engine import AuditEngine

app = FastAPI(title="Advanced Energy Audit API", version="2.1")

# Enable CORS for Lovable.app or local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In prod, strictly set this to ["https://energy-assessment.lovable.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_DIR = "models_advanced"
MODELS = {}
audit_engine = None
BENCHMARK_PATH = f"{MODEL_DIR}/benchmark_data.json"

# Constants
AVG_ELEC_RATE = 0.14  # $/kWh
AVG_GAS_RATE = 1.20   # $/Therm (approx 29.3 kWh equivalent... let's stick to kWh for simplicity or convert)
# 1 Therm = 29.3 kWh. $1.20/Therm -> $0.04/kWh equiv for Gas.
# Blended Rate approx $0.10/kWh for simplicity or separate if we predicted fuels.
# Our models predict kBTU. 
# 1 kBTU = 0.293 kWh.
KBTU_TO_KWH = 0.293
CO2_PER_KWH = 0.85 # lbs per kWh (approx US grid avg)
LBS_TO_TONS = 0.0005

def calculate_grade(percentile):
    if percentile > 80: return "A"
    if percentile > 60: return "B"
    if percentile > 40: return "C"
    if percentile > 20: return "D"
    return "F"

def calculate_co2(total_kbtu):
    total_kwh = total_kbtu * KBTU_TO_KWH
    return round(total_kwh * CO2_PER_KWH * LBS_TO_TONS, 2)
class HomeProfile(BaseModel):
    # Numeric
    TOTSQFT_EN: float
    HDD65: float
    CDD65: float
    NHSLDMEM: int
    NUMFRIG: int = 1
    NUMFREEZ: int = 0
    TVCOLOR: int = 2
    NUMLAPTOP: int = 1
    NUMTABLET: int = 1
    NUMSMPHONE: int = 2
    
    # Categorical
    DIVISION: str
    TYPEHUQ: str
    UATYP10: str = "U" # Urban default
    YEARMADERANGE: str
    WALLTYPE: str = "1" # Wood default
    ROOFTYPE: str = "1" # Shingle
    WINDOWS: str = "3" # Average frequency
    ADQINSUL: str = "2" # Adequate
    DRAFTY: str = "3" # Some drafts
    EQUIPM: str = "3" # Furnace
    FUELHEAT: str = "1" # Natural Gas
    ACEQUIPM_PUB: str = "1" # Central AC
    WHEATSIZ: str = "3" # Medium
    FUELH2O: str = "1" # Gas
    WHEATBKT: str = "0" # Not tankless
    AGECWASH: str = "3" # Average age
    AGEDW: str = "3"
    AGERFRI1: str = "3"
    LGTINLED: str = "2" # Some LED
    SMARTMETER: str = "0"
    SDESCENT: str = "0"
    EDUCATION: str = "4" # Bachelor's
    EMPLOYHH: str = "1" # Full time
    PAYHELP: str = "0"
    NOHEATBROKE: str = "0"

@app.on_event("startup")
def load_models():
    """Load advanced ML artifacts."""
    global MODELS, audit_engine
    try:
        # Load Transformer
        with open(f"{MODEL_DIR}/preprocessor.pkl", "rb") as f:
            MODELS['preprocessor'] = pickle.load(f)
            
        # Load Feature Metadata
        with open(f"{MODEL_DIR}/feature_meta.pkl", "rb") as f:
            MODELS['meta'] = pickle.load(f)

        # Load Benchmarks (JSON)
        if os.path.exists(BENCHMARK_PATH):
            with open(BENCHMARK_PATH, "r") as f:
                import json
                MODELS['benchmarks'] = json.load(f)
                
        # Initialize Audit Engine
        audit_engine = AuditEngine(benchmarks=MODELS.get('benchmarks', {}))

        # Load XGBoost Models
        for name in ['total_kbtu', 'heating_kbtu', 'cooling_kbtu', 'water_kbtu', 'baseload_kbtu']:
            with open(f"{MODEL_DIR}/xgb_{name}.pkl", "rb") as f:
                MODELS[name] = pickle.load(f)
                
        print("Advanced models loaded successfully.")
    except Exception as e:
        print(f"Error loading models: {e}")

@app.post("/audit")
def create_audit(profile: HomeProfile):
    if not MODELS:
        raise HTTPException(status_code=503, detail="Models not loaded")

    # 1. Prepare Data & Feature Engineering
    input_data = profile.dict()
    df_input = pd.DataFrame([input_data])
    
    # --- SENIOR ENGINEER: On-the-fly Feature Engineering ---
    # Must match train_advanced.py logic EXACTLY
    if 'HDD65' in df_input.columns and 'TOTSQFT_EN' in df_input.columns:
        df_input['HDD_x_SQFT'] = df_input['HDD65'] * df_input['TOTSQFT_EN']
    else:
        df_input['HDD_x_SQFT'] = 0
        
    if 'CDD65' in df_input.columns and 'TOTSQFT_EN' in df_input.columns:
        df_input['CDD_x_SQFT'] = df_input['CDD65'] * df_input['TOTSQFT_EN']
    else:
        df_input['CDD_x_SQFT'] = 0

    if 'TOTSQFT_EN' in df_input.columns and 'NHSLDMEM' in df_input.columns:
        members = df_input['NHSLDMEM'].replace(0, 1) # Avoid div/0
        df_input['SQFT_PER_CAPITA'] = df_input['TOTSQFT_EN'] / members
    else:
        df_input['SQFT_PER_CAPITA'] = 0
        
    # Ensure all expected columns exist (fill defaults if missing)
    expected_cols = MODELS['meta']['numeric'] + MODELS['meta']['categorical']
    for c in expected_cols:
        if c not in df_input.columns:
            df_input[c] = 0 if c in MODELS['meta']['numeric'] else "Unknown"
            
    # Reorder to match training
    df_input = df_input[expected_cols]
    
    # Ensure all categoricals are strings (Pydantic might convert some if user sends int)
    for cat in MODELS['meta']['categorical']:
        if cat in df_input.columns:
            df_input[cat] = df_input[cat].astype(str)
            
    # Preprocess
    try:
        X_processed = MODELS['preprocessor'].transform(df_input)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing error: {str(e)}")
    
    # 2. Inference
    breakdown = {}
    total_kbtu_pred = 0
    
    for name, model in MODELS.items():
        if name in ['meta', 'preprocessor', 'benchmarks']: continue
        pred = model.predict(X_processed)[0]
        val = max(0, float(pred)) # No negative energy
        breakdown[name] = val
        
    # Sum components for consistent Total? 
    # Or use Total Model? 
    # Usually sum of components is better for disaggregation consistency.
    # But Total Model might be more accurate for the top line.
    # Let's use Total Model for Top Line, and normalize components to match it?
    # For now, let's just use the Total Model Prediction as the Authority.
    
    total_kbtu = breakdown.get('total_kbtu', 0)
    
    # 4. Financials
    BLENDED_RATE = 0.035
    annual_cost = total_kbtu * BLENDED_RATE
    
    # 5. Benchmarking & Scoring
    # ... (Keep existing Logic or move to AuditEngine? let's keep score logic here for now) ...
    # Reuse previous logic for efficiency score
    try:
        bench_db = MODELS.get('benchmarks', {})
        region_key = profile.DIVISION.split(" ")[0]
        if region_key not in ["Northeast", "Midwest", "South", "West"]:
            region_key = "National"
        target_eui = bench_db.get('eui', {}).get(region_key, 35.0)
        user_eui = total_kbtu / profile.TOTSQFT_EN
        ratio = user_eui / (target_eui + 0.1)
        raw_score = 100 - ((ratio - 0.5) * 50) 
        efficiency_score = max(0, min(100, raw_score))
        grade = calculate_grade(efficiency_score)
    except Exception as e:
        print(f"Benchmark error: {e}")
        efficiency_score = 75
        grade = "B"

    # 6. Recommendations (Using Expert System)
    # Pass profile (dict), breakdown, and total to engine
    recs = audit_engine.generate_recommendations(input_data, breakdown, total_kbtu)
    
    # Construct Response
    return {
        "status": "success",
        "score": {
            "value": round(efficiency_score),
            "grade": grade,
            "label": "Excellent" if grade in ["A","B"] else "Improvement Needed"
        },
        "financials": {
            "annual_cost": round(annual_cost),
            "monthly_bill": round(annual_cost/12),
            "potential_savings": round(sum(r['annual_savings'] for r in recs))
        },
        "usage": {
            "total_kbtu": round(total_kbtu),
            "total_kwh_equiv": round(total_kbtu * KBTU_TO_KWH),
            "eui": round(user_eui, 1),
            "carbon_tons": calculate_co2(total_kbtu)
        },
        "breakdown_pct": {
            "heating": round(breakdown.get('heating_kbtu',0)/total_kbtu * 100) if total_kbtu else 0,
            "cooling": round(breakdown.get('cooling_kbtu',0)/total_kbtu * 100) if total_kbtu else 0,
            "water_heating": round(breakdown.get('water_kbtu',0)/total_kbtu * 100) if total_kbtu else 0,
            "lighting": 10,
            "appliances": 15
        },
        "recommendations": recs
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
