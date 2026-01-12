
"""
Audit Engine: Expert System for Home Energy Recommendations
------------------------------------------------------------
Implements logical rules to mimic a professional energy auditor.
Combines predictive data (ML models) with physical constraints.
"""

class AuditEngine:
    def __init__(self, benchmarks=None, rates=None):
        self.benchmarks = benchmarks or {}
        self.rates = rates or {"elec": 0.14, "gas": 1.50, "blended": 0.035}

    def generate_recommendations(self, profile, usage_breakdown, total_kbtu):
        """
        Main entry point. Returns a list of Recommendation objects.
        """
        recs = []
        
        # 1. Heating & Envelope Analysis
        recs.extend(self._analyze_heating(profile, usage_breakdown, total_kbtu))
        
        # 2. Cooling & Windows Analysis
        recs.extend(self._analyze_cooling(profile, usage_breakdown, total_kbtu))
        
        # 3. Water Heating Analysis
        recs.extend(self._analyze_water_heating(profile, usage_breakdown))
        
        # 4. Baseload & Appliances
        recs.extend(self._analyze_baseload(profile, usage_breakdown))
        
        # 5. Solar Potential (Always check)
        recs.extend(self._analyze_solar(profile, total_kbtu))

        # Sort by ROI (Years to Payback - ascending)
        return sorted(recs, key=lambda x: x['roi_years'])

    def _analyze_heating(self, p, breakdown, total):
        recs = []
        heat_kbtu = breakdown.get('heating_kbtu', 0)
        pct_heat = heat_kbtu / (total + 1)
        
        # Rule 1: Insulation Check
        # If heating is significant (>30%) AND insulation is reported as "Poor" or House is Old (<1980) and not updated
        is_old = False
        try:
             year = int(p.get('YEARMADERANGE', 2000))
             if year < 1980: is_old = True
        except: pass
        
        poor_insul = p.get('ADQINSUL', 2) in [2, 3] # 2=Adequate, 3=Poor? Varies by encoding. Let's assume input is raw.
        # Check specific variable mapping in main for ADQINSUL.
        
        if pct_heat > 0.30 and (poor_insul or is_old):
            savings = heat_kbtu * 0.15 * self.rates['blended'] # 15% savings assumption
            cost = 2500 # Avg attic insulation
            if savings > 50:
                recs.append({
                    "title": "Upgrade Attic Insulation",
                    "priority": "High" if savings > 200 else "Medium",
                    "icon": "Insulation",
                    "description": "Your heating load is high. Adding R-49 attic insulation can reduce heat loss.",
                    "annual_savings": round(savings),
                    "cost": cost,
                    "roi_years": round(cost / savings, 1),
                    "co2_reduction": round(savings / self.rates['blended'] * 0.0004, 2) # Rough Co2
                })

        # Rule 2: Equipment Upgrade
        # If heating system is old (EQUIPMAGE?)
        return recs

    def _analyze_cooling(self, p, breakdown, total):
        recs = []
        cool_kbtu = breakdown.get('cooling_kbtu', 0)
        pct_cool = cool_kbtu / (total + 1)
        
        # Rule: Windows / Sealing
        if pct_cool > 0.15: # Significant cooling load
             savings = cool_kbtu * 0.10 * self.rates['blended']
             cost = 400
             recs.append({
                "title": "Air Sealing & Weatherstripping",
                "priority": "Medium",
                "icon": "Wind",
                "description": "Seal gaps around windows/doors to keep cool air in.",
                "annual_savings": round(savings),
                "cost": cost,
                "roi_years": round(cost/savings, 1),
                "co2_reduction": round(savings/self.rates['blended']*0.0004, 2)
             })
        return recs

    def _analyze_water_heating(self, p, breakdown):
        recs = []
        wh_kbtu = breakdown.get('water_kbtu', 0)
        
        # Rule: Switch to Heat Pump Water Heater if using Electric Resistance
        # Assuming we can infer electricity usage or fuel type.
        try:
             fuel_h2o = int(p.get('FUELH2O', 0))
        except:
             fuel_h2o = 0
             
        # If 'FUELH2O' == 1 (Electricity) -> Recommend HPWH
        if fuel_h2o == 1 and wh_kbtu > 10000: # High usage
            savings = wh_kbtu * 0.60 * self.rates['blended'] # 60% savings
            cost = 2500
            recs.append({
                "title": "Heat Pump Water Heater",
                "priority": "High",
                "icon": "Water",
                "description": "Switching to a Hybrid/Heat Pump unit saves ~60% on water heating.",
                "annual_savings": round(savings),
                "cost": cost,
                "roi_years": round(cost/savings, 1),
                "co2_reduction": round(savings/self.rates['blended']*0.0004, 2)
            })
        return recs

    def _analyze_baseload(self, p, breakdown):
        recs = []
        base_kbtu = breakdown.get('baseload_kbtu', 0)
        
        # Rule: Old Refrigerator
        try:
            num_frig = int(p.get('NUMFRIG', 1))
            age_frig = int(p.get('AGERFRI1', 3))
        except:
            num_frig = 1
            age_frig = 3
            
        if num_frig > 1 or age_frig > 3: # 3 might mean 'Older than 10 yrs'
             savings = 500 * self.rates['blended'] 
             cost = 800
             recs.append({
                "title": "Upgrade / Remove 2nd Fridge",
                "priority": "Medium",
                "icon": "Fridge",
                "description": "Older fridges are energy hogs. Upgrade to Energy Star.",
                "annual_savings": round(savings),
                "cost": cost,
                "roi_years": round(cost/savings, 1),
                "co2_reduction": round(savings/self.rates['blended']*0.0004, 2)
             })
        return recs

    def _analyze_solar(self, p, total_kbtu):
        recs = []
        # Simple Solar logic
        prod = 6000 # kWh/yr
        savings = prod * self.rates['elec'] # Use Elec rate specifically
        cost = 15000
        
        recs.append({
                "title": "Install 6kW Solar System",
                "priority": "High" if savings > 1000 else "Medium",
                "icon": "Solar",
                "description": "Generate your own clean power vs buying from grid.",
                "annual_savings": round(savings),
                "cost": cost,
                "roi_years": round(cost/savings, 1),
                "co2_reduction": round(prod * 0.0004, 2) # Tons
        })
        return recs
