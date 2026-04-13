# Feature Reduction Notes

## Objective
Reduce the model input feature set from the original broader configuration to a smaller curated subset while keeping training, inference, and validation aligned.

## Changes Made
- Reduced the feature set used in `train_advanced.py`
- Updated engineered features to the reduced subset
- Updated `main.py` so inference-side feature engineering matches training
- Updated `test_feature_engineering.py` to validate the reduced engineered feature set
- Retrained model artifacts using the reduced feature configuration

## Result
- Reduced-feature retraining completed successfully
- Feature engineering validation test passes
- Training/inference/test feature engineering is now aligned
- Baseload prediction remains the weakest target and may need future tuning

## Files Updated
- `train_advanced.py`
- `main.py`
- `test_feature_engineering.py`
- `models_advanced/feature_meta.pkl`
- `models_advanced/preprocessor.pkl`
- `models_advanced/xgb_total_kbtu.pkl`
- `models_advanced/xgb_heating_kbtu.pkl`
- `models_advanced/xgb_cooling_kbtu.pkl`
- `models_advanced/xgb_water_kbtu.pkl`
- `models_advanced/xgb_baseload_kbtu.pkl`