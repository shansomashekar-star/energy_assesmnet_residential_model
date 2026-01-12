
from fastapi.testclient import TestClient
from main import app
import json

def run_scenario(name, profile):
    print(f"\n>>> Running Scenario: {name}")
    print(f"    Profile: {profile['TOTSQFT_EN']} sqft, Built: {profile['YEARMADERANGE']}, Insulation: {profile['ADQINSUL']}")
    
    with TestClient(app) as client:
        response = client.post("/audit", json=profile)
        if response.status_code == 200:
            data = response.json()
            score = data['score']
            fins = data['financials']
            print(f"    [RESULT] Grade: {score['grade']} ({score['value']}/100)")
            print(f"    [RESULT] Est. Annual Cost: ${fins['annual_cost']}")
            print(f"    [RESULT] Carbon: {data['usage']['carbon_tons']} tons")
            print(f"    [RESULT] Recommendations: {len(data['recommendations'])} found")
            for i, rec in enumerate(data['recommendations'][:3]): # Show top 3
                print(f"      {i+1}. {rec['title']} (ROI: {rec['roi_years']} yrs) - {rec['priority']}")
        else:
            print(f"    [ERROR] {response.text}")

if __name__ == "__main__":
    # Scenario A: The Energy Hog
    # 1950s, Poor Insulation, Single Pane Windows, Old Furnace
    hog = {
        "TOTSQFT_EN": 3500,
        "HDD65": 6000, 
        "CDD65": 800,  
        "NHSLDMEM": 4,
        "DIVISION": "New England",
        "TYPEHUQ": "2", 
        "YEARMADERANGE": "2", # 1950s
        "WALLTYPE": "1",
        "ROOFTYPE": "1",
        "WINDOWS": "1", # Few/Single
        "ADQINSUL": "3", # Poor
        "DRAFTY": "4", # Drafty
        "EQUIPM": "3", # Furnace
        "FUELHEAT": "1", 
        "ACEQUIPM_PUB": "1", 
        "WHEATSIZ": "3",
        "FUELH2O": "1",
        "WHEATBKT": "0",
        "AGECWASH": "3",
        "AGEDW": "3",
        "AGERFRI1": "3",
        "LGTINLED": "3", # No LED
        "SMARTMETER": "0",
        "SDESCENT": "0",
        "EDUCATION": "4",
        "EMPLOYHH": "1",
        "PAYHELP": "0",
        "NOHEATBROKE": "0"
    }

    # Scenario B: The Eco Star
    # 2010s, Good Insulation, Double Pane, Heat Pump (Proxy)
    eco = hog.copy()
    eco.update({
        "YEARMADERANGE": "7", # 2010-2015
        "ADQINSUL": "1", # Well Insulated
        "DRAFTY": "1", # Never Drafty
        "WINDOWS": "5", # Many (but efficient usually implied by age/code)
        "LGTINLED": "1", # All LED
        "SMARTMETER": "1"
    })

    run_scenario("The Energy Hog (1950s, Uninsulated)", hog)
    run_scenario("The Eco Star (2015, Well Insulated)", eco)
