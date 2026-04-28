from typing import List, Dict, Any


def normalize_bill(bill: Dict[str, Any]) -> Dict[str, Any]:
    usage_kwh = float(bill.get("electricity_kwh", 0))
    total_cost = float(bill.get("bill_amount_usd", 0))

    return {
        **bill,
        "usage_kwh": usage_kwh,
        "total_cost": total_cost,
    }


def choose_forecast_mode(valid_bill_count: int) -> str:
    if valid_bill_count < 3:
        return "simulation"
    elif valid_bill_count < 6:
        return "blended_early"
    elif valid_bill_count < 12:
        return "blended_mid"
    return "time_series"


def build_forecast(raw_bills: List[Dict[str, Any]]) -> Dict[str, Any]:
    bills = [normalize_bill(bill) for bill in raw_bills]
    bills = [bill for bill in bills if bill["usage_kwh"] > 0 and bill["total_cost"] > 0]

    mode = choose_forecast_mode(len(bills))

    if bills:
        latest = bills[-1]
        base_kwh = latest["usage_kwh"]
        base_cost = latest["total_cost"]
    else:
        base_kwh = 850
        base_cost = 142.50

    seasonal = [1.02, 0.98, 0.95, 0.93, 0.96, 1.05, 1.12, 1.15, 1.06, 0.99, 0.97, 1.02]

    projected_usage = []
    projected_cost = []

    for month_index in range(12):
        usage = base_kwh * seasonal[month_index]
        cost = base_cost * seasonal[month_index]

        projected_usage.append(round(usage, 2))
        projected_cost.append(round(cost, 2))

    confidence = "low"
    if len(bills) >= 3:
        confidence = "medium"
    if len(bills) >= 12:
        confidence = "high"

    return {
        "mode": mode,
        "bill_count": len(bills),
        "confidence": confidence,
        "projected_monthly_usage_kwh": projected_usage,
        "projected_monthly_cost_usd": projected_cost,
        "explanation": f"Forecast generated using {len(bills)} saved bill record(s)."
    }