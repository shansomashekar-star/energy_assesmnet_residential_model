
from fastapi.testclient import TestClient
from main import app
import json

def test_audit():
    print("--- Starting Advanced Energy Audit Simulation ---\n")
    
    with TestClient(app) as client:
        # 1. Simulate a Detailed Client Request
        # Profile: Large older home in Northeast (Cold), educated owner, gas heat, unfinished basement
        payload = {
            # Continuous
            "TOTSQFT_EN": 3500,
            "HDD65": 7000, 
            "CDD65": 500,  
            "NHSLDMEM": 5,
            "NUMFRIG": 2,
            "NUMFREEZ": 1,
            
            # Categorical
            "DIVISION": "New England", #####
            "TYPEHUQ": "2", # Single Family Detached
            "UATYP10": "U", # Urban
            "YEARMADERANGE": "2", # 1950-1959
            "WALLTYPE": "2", # Brick
            "ROOFTYPE": "1", # Shingle
            "WINDOWS": "4", # Many windows
            "ADQINSUL": "3", # Poor insulation
            "DRAFTY": "4", # Very drafty
            "EQUIPM": "3", # Central Furnace
            "FUELHEAT": "1", # Nat Gas
            "ACEQUIPM_PUB": "1", # Central AC
            "WHEATSIZ": "3", # Med
            "FUELH2O": "1", # Gas
            "WHEATBKT": "0", # Tank
            "AGECWASH": "3",
            "AGEDW": "3",
            "AGERFRI1": "3",
            "LGTINLED": "1", # All LED
            "SMARTMETER": "1",
            "SDESCENT": "0",
            "EDUCATION": "5", # Graduate Degree
            "EMPLOYHH": "1",
            "PAYHELP": "0",
            "NOHEATBROKE": "0"
        }
        
        # Note: 'DIVISION' categorical in training was likely coded as string names (e.g. 'New England') 
        # because we read the CSV directly without mapping codes? 
        # Wait, the CSV has 'DIVISION' as string names usually?
        # Let's check the CSV head output from Step 54:
        # DIVISION is 'West South Central', 'Mountain South', etc. 
        # So "New England" is correct.
        
        print(f"Input Profile (Subset): {json.dumps({k:v for k,v in payload.items() if k in ['TOTSQFT_EN', 'DIVISION']}, indent=2)}")
        
        # 2. Call the API
        response = client.post("/audit", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Advanced Audit Report ---")
            print(json.dumps(data, indent=2))
            
            # Validation
            assert data["status"] == "success"
            assert "score" in data
            assert "financials" in data
            print("\n[SUCCESS] Advanced model inference validated.")
        else:
            print(f"\n[ERROR] API Request Failed: {response.text}")

if __name__ == "__main__":
    test_audit()
