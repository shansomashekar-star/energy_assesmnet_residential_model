from fastapi import FastAPI, HTTPException
from typing import Any, Dict, List, Union
from pathlib import Path
import joblib
import pandas as pd

app = FastAPI(title="Commercial CBECS SiteEUI API", version="1.0")

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "model.joblib"
model = None
required_columns: List[str] = []

def _extract_required_columns(pipeline) -> List[str]:
    cols: List[str] = []
    try:
        preprocess = pipeline.named_steps.get("preprocess")
        if preprocess:
            for _, __, columns in preprocess.transformers:
                if isinstance(columns, list):
                    cols.extend(columns)
    except Exception:
        pass
    out, seen = [], set()
    for c in cols:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out

@app.on_event("startup")
def load_model():
    global model, required_columns
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Missing model at {MODEL_PATH}. Put model.joblib in commercial/models/")
    model = joblib.load(MODEL_PATH)
    required_columns = _extract_required_columns(model)

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}

@app.get("/schema")
def schema():
    return {"required_columns": required_columns}

@app.post("/predict")
def predict(payload: Union[Dict[str, Any], List[Dict[str, Any]]]):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    rows = payload if isinstance(payload, list) else [payload]
    df = pd.DataFrame(rows)

    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Missing required input fields",
                    "missing_count": len(missing),
                    "missing_fields_sample": missing[:50],
                    "tip": "Call GET /schema to see all required fields."
                },
            )
        df = df[required_columns]

    preds = model.predict(df).tolist()
    return {"predictions": preds if isinstance(payload, list) else preds[0]}
