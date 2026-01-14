
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Union
import pickle
import pandas as pd
import numpy as np
import os
from audit_engine import AuditEngine
from report_generator import AuditReport
from utility_rates import UtilityRates

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
    # Core Numeric Features
    TOTSQFT_EN: float
    HDD65: float
    CDD65: float
    NHSLDMEM: int
    
    # Building Envelope Numeric
    STORIES: Optional[int] = 1
    DOOR1SUM: Optional[int] = 3
    TREESHAD: Optional[int] = 2
    
    # HVAC Numeric
    ACEQUIPAGE: Optional[int] = 3
    TEMPHOME: Optional[int] = 70
    TEMPGONE: Optional[int] = 65
    TEMPNITE: Optional[int] = 68
    
    # Appliance Numeric
    NUMFRIG: int = 1
    NUMFREEZ: int = 0
    AGERFRI1: Optional[int] = 3
    AGERFRI2: Optional[int] = 0
    AGEFRZ1: Optional[int] = 0
    AMTMICRO: Optional[int] = 2
    WASHLOAD: Optional[int] = 3
    WASHTEMP: Optional[int] = 2
    TVCOLOR: int = 2
    TVONWD1: Optional[int] = 5
    TVONWE1: Optional[int] = 6
    NUMLAPTOP: int = 1
    NUMTABLET: int = 1
    NUMSMPHONE: int = 2
    
    # Water Heating Numeric
    WHEATSIZ: Optional[int] = 3
    WHEATAGE: Optional[int] = 3
    MORETHAN1H2O: Optional[int] = 0
    
    # Lighting Numeric
    LGTINLED: Optional[int] = 2
    LGTINCFL: Optional[int] = 2
    LGTINCAN: Optional[int] = 3
    LGTIN1TO4: Optional[int] = 2
    LGTIN4TO8: Optional[int] = 2
    LGTINMORE8: Optional[int] = 2
    LGTOUTANY: Optional[int] = 1
    LGTOUTNITE: Optional[int] = 1
    
    # Behavioral Numeric
    ATHOME: Optional[int] = 3
    MONEYPY: Optional[int] = 4
    
    # Categorical Features
    DIVISION: str
    TYPEHUQ: str
    UATYP10: str = "U"
    YEARMADERANGE: str
    WALLTYPE: str = "1"
    ROOFTYPE: str = "1"
    WINDOWS: str = "3"
    TYPEGLASS: Optional[str] = "2"
    WINFRAME: Optional[str] = "1"
    ADQINSUL: str = "2"
    DRAFTY: str = "3"
    ATTIC: Optional[str] = "1"
    ATTICFIN: Optional[str] = "1"
    CELLAR: Optional[str] = "0"
    CRAWL: Optional[str] = "0"
    CONCRETE: Optional[str] = "1"
    EQUIPM: str = "3"
    FUELHEAT: str = "1"
    ACEQUIPM_PUB: str = "1"
    COOLTYPE: Optional[str] = "1"
    THERMAIN: Optional[str] = "1"
    PROTHERM: Optional[str] = "0"
    EQUIPAUX: Optional[str] = "0"
    DUCTS: Optional[str] = "1"
    DUCTINSUL: Optional[str] = "1"
    HEATHOME: Optional[str] = "1"
    RANGE: Optional[str] = "1"
    RANGEFUEL: Optional[str] = "1"
    RANGEINDT: Optional[str] = "0"
    OVEN: Optional[str] = "1"
    OVENFUEL: Optional[str] = "1"
    MICRO: Optional[str] = "1"
    DISHWASH: Optional[str] = "1"
    DWASHUSE: Optional[str] = "3"
    AGEDW: Optional[str] = "3"
    CWASHER: Optional[str] = "1"
    AGECWASH: Optional[str] = "3"
    DRYER: Optional[str] = "1"
    DRYRFUEL: Optional[str] = "1"
    AGECDRYER: Optional[str] = "3"
    FUELH2O: str = "1"
    WHEATBKT: str = "0"
    ELWATER: Optional[str] = "0"
    FOWATER: Optional[str] = "0"
    LPWATER: Optional[str] = "0"
    SOLWATER: Optional[str] = "0"
    SMARTMETER: str = "0"
    EDUCATION: str = "4"
    EMPLOYHH: str = "1"
    SDESCENT: str = "0"
    PAYHELP: str = "0"
    NOHEATBROKE: str = "0"
    
    # Optional custom utility rates
    custom_elec_rate: Optional[float] = None
    custom_gas_rate: Optional[float] = None
    
    # Additional fields from multi-step form
    STORIES: Optional[int] = 1
    monthly_bill: Optional[float] = None  # For validation/calibration
    has_solar: Optional[int] = 0

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
                
        # Initialize Audit Engine (will be re-initialized per request with rates)
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
    
    # --- Feature Engineering (must match train_advanced.py exactly) ---
    # Basic interactions
    if 'HDD65' in df_input.columns and 'TOTSQFT_EN' in df_input.columns:
        df_input['HDD_x_SQFT'] = df_input['HDD65'] * df_input['TOTSQFT_EN']
    else:
        df_input['HDD_x_SQFT'] = 0
        
    if 'CDD65' in df_input.columns and 'TOTSQFT_EN' in df_input.columns:
        df_input['CDD_x_SQFT'] = df_input['CDD65'] * df_input['TOTSQFT_EN']
    else:
        df_input['CDD_x_SQFT'] = 0

    if 'TOTSQFT_EN' in df_input.columns and 'NHSLDMEM' in df_input.columns:
        members = df_input['NHSLDMEM'].replace(0, 1)
        df_input['SQFT_PER_CAPITA'] = df_input['TOTSQFT_EN'] / members
    else:
        df_input['SQFT_PER_CAPITA'] = 0
    
    # Advanced interaction features
    if 'ADQINSUL' in df_input.columns:
        insulation_factor = df_input['ADQINSUL'].astype(str).replace({'1': 1.0, '2': 0.7, '3': 0.4}).fillna(0.7)
    else:
        insulation_factor = pd.Series([0.7] * len(df_input))
    df_input['HDD_x_SQFT_x_INSUL'] = df_input['HDD65'] * df_input['TOTSQFT_EN'] * insulation_factor
    
    if 'WINDOWS' in df_input.columns:
        window_factor = pd.to_numeric(df_input['WINDOWS'], errors='coerce').fillna(3) / 5.0
    else:
        window_factor = pd.Series([0.6] * len(df_input))
    df_input['CDD_x_SQFT_x_WINDOWS'] = df_input['CDD65'] * df_input['TOTSQFT_EN'] * window_factor
    
    if 'AGERFRI1' in df_input.columns:
        age_frig = pd.to_numeric(df_input['AGERFRI1'], errors='coerce').fillna(3)
    else:
        age_frig = pd.Series([3] * len(df_input))
    if 'ACEQUIPAGE' in df_input.columns:
        age_hvac = pd.to_numeric(df_input['ACEQUIPAGE'], errors='coerce').fillna(3)
    else:
        age_hvac = pd.Series([3] * len(df_input))
    df_input['AGE_x_EFFICIENCY'] = (age_frig + age_hvac) / 12.0
    
    df_input['OCCUPANCY_x_BASELOAD'] = df_input['NHSLDMEM'] * df_input['TOTSQFT_EN'] / 1000.0
    
    if 'WINDOWS' in df_input.columns:
        window_count_proxy = pd.to_numeric(df_input['WINDOWS'], errors='coerce').fillna(3)
    else:
        window_count_proxy = pd.Series([3] * len(df_input))
    df_input['WINDOW_AREA_EST'] = df_input['TOTSQFT_EN'] * (window_count_proxy / 5.0) * 0.15
    
    if 'EQUIPM' in df_input.columns:
        equip_type = pd.to_numeric(df_input['EQUIPM'], errors='coerce').fillna(3)
        heating_efficiency = equip_type.map({1: 0.3, 2: 0.6, 3: 0.7, 4: 0.65, 5: 0.8}).fillna(0.7)
    else:
        heating_efficiency = pd.Series([0.7] * len(df_input))
    df_input['HEATING_EFF_PROXY'] = heating_efficiency
    
    if 'ACEQUIPM_PUB' in df_input.columns:
        cool_type = pd.to_numeric(df_input['ACEQUIPM_PUB'], errors='coerce').fillna(1)
        cooling_efficiency = cool_type.map({1: 0.6, 2: 0.5, 3: 0.7, 4: 0.8}).fillna(0.6)
    else:
        cooling_efficiency = pd.Series([0.6] * len(df_input))
    df_input['COOLING_EFF_PROXY'] = cooling_efficiency
        
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
    
    # 3.5. Calibrate predictions using monthly bill if provided
    monthly_bill = input_data.get('monthly_bill') or input_data.get('monthlyBill')
    if monthly_bill and monthly_bill > 0:
        # User provided actual monthly bill - use it to calibrate
        annual_cost_from_bill = monthly_bill * 12
        # Estimate kBTU from bill using regional rates
        rates_temp = UtilityRates(division=profile.DIVISION)
        # Approximate: $0.10-0.15 per kBTU blended rate
        blended_rate_per_kbtu = rates_temp.kbtu_to_dollars(1, 'blended')
        if blended_rate_per_kbtu > 0:
            estimated_kbtu_from_bill = annual_cost_from_bill / blended_rate_per_kbtu
            
            # Blend predicted and bill-based estimates (70% prediction, 30% bill-based)
            # This accounts for user's actual usage patterns
            calibration_factor = 0.7
            total_kbtu = (total_kbtu * calibration_factor) + (estimated_kbtu_from_bill * (1 - calibration_factor))
            
            # Adjust breakdown proportionally
            original_total = breakdown.get('total_kbtu', total_kbtu)
            if original_total > 0:
                scale_factor = total_kbtu / original_total
                for key in breakdown:
                    if key != 'total_kbtu':
                        breakdown[key] = breakdown[key] * scale_factor
                breakdown['total_kbtu'] = total_kbtu
    
    # 4. Initialize utility rates (with custom rates if provided)
    custom_rates = {}
    if profile.custom_elec_rate:
        custom_rates['elec'] = profile.custom_elec_rate
    if profile.custom_gas_rate:
        custom_rates['gas'] = profile.custom_gas_rate
    
    rates = UtilityRates(division=profile.DIVISION, custom_rates=custom_rates if custom_rates else None)
    
    # 5. Climate data for savings calculator
    climate_data = {
        'hdd': profile.HDD65,
        'cdd': profile.CDD65
    }
    
    # 6. Initialize audit engine with rates and climate data
    audit_engine = AuditEngine(
        benchmarks=MODELS.get('benchmarks', {}),
        rates=rates,
        climate_data=climate_data
    )
    
    # 7. Generate recommendations
    recs = audit_engine.generate_recommendations(input_data, breakdown, total_kbtu)
    
    # 8. Generate comprehensive report
    report_generator = AuditReport(
        profile=input_data,
        usage_data=breakdown,
        recommendations=recs,
        benchmarks=MODELS.get('benchmarks', {}),
        rates=rates
    )
    
    # Return comprehensive report
    return report_generator.generate_full_report()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
