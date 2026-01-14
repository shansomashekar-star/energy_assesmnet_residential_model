"""
Simple API Test
---------------
Quick test to verify the API is working before using the frontend.
"""

import requests
import json

API_URL = "http://localhost:8001/audit"

# Sample home profile
test_profile = {
    "TOTSQFT_EN": 2400,
    "HDD65": 5500,
    "CDD65": 800,
    "NHSLDMEM": 4,
    "DIVISION": "Northeast",
    "TYPEHUQ": "2",
    "YEARMADERANGE": "5",
    "ADQINSUL": "2",
    "DRAFTY": "3",
    "EQUIPM": "3",
    "FUELHEAT": "1",
    "ACEQUIPM_PUB": "1",
    "FUELH2O": "1",
    "NUMFRIG": 1,
    "AGERFRI1": "3",
    "LGTINLED": "2",
    "UATYP10": "U",
    "WALLTYPE": "1",
    "ROOFTYPE": "1",
    "WINDOWS": "3",
    "WHEATSIZ": "3",
    "WHEATBKT": "0",
    "AGECWASH": "3",
    "AGEDW": "3",
    "SMARTMETER": "0",
    "EDUCATION": "4",
    "EMPLOYHH": "1",
    "SDESCENT": "0",
    "PAYHELP": "0",
    "NOHEATBROKE": "0"
}

def test_api():
    """Test the API with a sample profile."""
    print("=" * 60)
    print("Testing Energy Assessment API")
    print("=" * 60)
    print(f"\nAPI URL: {API_URL}")
    print("\nSending request...")
    
    try:
        response = requests.post(API_URL, json=test_profile, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✓ API Response Received Successfully!")
            print("\n" + "=" * 60)
            print("RESULTS SUMMARY")
            print("=" * 60)
            
            # Energy Score
            if 'energy_score' in data:
                score = data['energy_score']
                print(f"\n📊 Energy Score: {score.get('overall', 'N/A')} (Grade: {score.get('grade', 'N/A')})")
                print(f"   {score.get('label', '')}")
            
            # Current Usage
            if 'current_usage' in data:
                usage = data['current_usage']
                print(f"\n💰 Annual Cost: ${usage.get('annual_cost', 0):,.0f}")
                print(f"   Monthly Average: ${usage.get('monthly_avg', 0):,.0f}")
                print(f"   Total Energy: {usage.get('total_kbtu', 0):,.0f} kBTU")
                print(f"   EUI: {usage.get('eui', 0):.1f} kBTU/sqft")
            
            # Recommendations
            if 'recommendations' in data:
                recs = data['recommendations']
                print(f"\n💡 Recommendations: {len(recs)} found")
                
                for i, rec in enumerate(recs[:5], 1):  # Show first 5
                    print(f"\n   {i}. {rec.get('title', 'N/A')}")
                    print(f"      Priority: {rec.get('priority', 'N/A')}")
                    print(f"      Annual Savings: ${rec.get('savings', {}).get('annual_dollars', 0):,.0f}")
                    print(f"      Cost: ${rec.get('cost', {}).get('estimate', 0):,.0f}")
                    print(f"      Payback: {rec.get('financial', {}).get('payback_years', 'N/A')} years")
            
            # Financial Summary
            if 'financial_summary' in data:
                financial = data['financial_summary']
                print(f"\n💵 Financial Summary:")
                print(f"   Total Investment: ${financial.get('total_investment', 0):,.0f}")
                print(f"   Annual Savings: ${financial.get('total_annual_savings', 0):,.0f}")
                print(f"   Lifetime Savings: ${financial.get('total_lifetime_savings', 0):,.0f}")
                print(f"   Average Payback: {financial.get('average_payback', 0):.1f} years")
            
            print("\n" + "=" * 60)
            print("✓ API Test PASSED")
            print("=" * 60)
            print("\nYou can now use the frontend.html file to test interactively!")
            
            return True
            
        else:
            print(f"✗ API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection Error: Could not connect to API")
        print("  Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)
