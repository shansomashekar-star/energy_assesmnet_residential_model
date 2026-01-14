"""
Test Savings Calculations
--------------------------
Validates physics-based savings formulas against known case studies.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from savings_calculator import SavingsCalculator
from utility_rates import UtilityRates


def test_insulation_savings():
    """Test insulation savings calculation."""
    print("Testing Insulation Savings...")
    
    calculator = SavingsCalculator(
        regional_rates={'division': 'Northeast'},
        climate_data={'hdd': 5500, 'cdd': 800}
    )
    
    # Test case: Upgrade attic from R-19 to R-49, 1500 sqft
    savings = calculator.calculate_insulation_savings(
        current_r_value=19,
        new_r_value=49,
        sqft=1500,
        surface_type='attic',
        heating_fuel='gas'
    )
    
    # Expected: Significant savings
    assert savings['annual_kbtu'] > 0, "Should have positive kBTU savings"
    assert savings['annual_dollars'] > 0, "Should have positive dollar savings"
    assert savings['annual_kbtu'] < 50000, "Savings should be reasonable"
    
    print(f"  ✓ Attic insulation: {savings['annual_dollars']:.0f} $/year")
    return True


def test_hvac_upgrade_savings():
    """Test HVAC upgrade savings calculation."""
    print("Testing HVAC Upgrade Savings...")
    
    calculator = SavingsCalculator(
        regional_rates={'division': 'Midwest'},
        climate_data={'hdd': 6500, 'cdd': 1000}
    )
    
    # Test case: Upgrade furnace from 78% to 95% AFUE, 45000 kBTU heating load
    savings = calculator.calculate_hvac_upgrade_savings(
        old_efficiency=78,
        new_efficiency=95,
        heating_load_kbtu=45000,
        fuel_type='gas'
    )
    
    assert savings['annual_kbtu'] > 0, "Should have positive savings"
    assert savings['annual_dollars'] > 100, "Should save at least $100/year"
    
    print(f"  ✓ Furnace upgrade: {savings['annual_dollars']:.0f} $/year")
    return True


def test_window_upgrade_savings():
    """Test window upgrade savings calculation."""
    print("Testing Window Upgrade Savings...")
    
    calculator = SavingsCalculator(
        regional_rates={'division': 'South'},
        climate_data={'hdd': 3000, 'cdd': 2000}
    )
    
    # Test case: Replace single-pane (U=1.2) with double-pane low-e (U=0.30), 300 sqft windows
    savings = calculator.calculate_window_upgrade_savings(
        old_u_factor=1.2,
        new_u_factor=0.30,
        window_sqft=300
    )
    
    assert savings['annual_kbtu'] > 0, "Should have positive savings"
    
    print(f"  ✓ Window upgrade: {savings['annual_dollars']:.0f} $/year")
    return True


def test_appliance_savings():
    """Test appliance upgrade savings calculation."""
    print("Testing Appliance Savings...")
    
    calculator = SavingsCalculator(regional_rates={'division': 'West'})
    
    # Test case: Old fridge (700 kWh/year) to ENERGY STAR (350 kWh/year)
    savings = calculator.calculate_appliance_savings(
        old_kwh_year=700,
        new_kwh_year=350
    )
    
    assert savings['annual_kwh'] == 350, "Should save 350 kWh/year"
    assert savings['annual_dollars'] > 0, "Should have positive dollar savings"
    
    print(f"  ✓ Appliance upgrade: {savings['annual_dollars']:.0f} $/year")
    return True


def test_solar_savings():
    """Test solar PV savings calculation."""
    print("Testing Solar PV Savings...")
    
    calculator = SavingsCalculator(
        regional_rates={'division': 'South'},
        climate_data={'hdd': 3000, 'cdd': 2000}
    )
    
    # Test case: 6kW system in South region
    savings = calculator.calculate_solar_savings(
        system_size_kw=6.0,
        roof_orientation='south',
        shading_factor=0.9
    )
    
    assert savings['annual_kwh'] > 0, "Should generate electricity"
    assert savings['annual_dollars'] > 500, "Should save significant amount"
    
    print(f"  ✓ Solar PV (6kW): {savings['annual_dollars']:.0f} $/year")
    return True


def test_payback_roi():
    """Test payback and ROI calculations."""
    print("Testing Payback & ROI Calculations...")
    
    calculator = SavingsCalculator()
    
    # Test case: $2500 cost, $500/year savings, $500 rebate
    financial = calculator.calculate_payback_roi(
        upfront_cost=2500,
        annual_savings_dollars=500,
        rebates=500
    )
    
    expected_payback = (2500 - 500) / 500  # 4 years
    assert abs(financial['payback_years'] - expected_payback) < 0.1, "Payback should be ~4 years"
    assert financial['roi_percent'] > 0, "ROI should be positive"
    
    print(f"  ✓ Payback: {financial['payback_years']:.1f} years")
    print(f"  ✓ ROI: {financial['roi_percent']:.1f}%")
    return True


def test_co2_reduction():
    """Test CO2 reduction calculations."""
    print("Testing CO2 Reduction Calculations...")
    
    calculator = SavingsCalculator()
    
    # Test case: 2000 kWh and 50 therms saved
    co2 = calculator.calculate_co2_reduction(
        annual_kwh_savings=2000,
        annual_therm_savings=50
    )
    
    # Expected: ~2-3 tons CO2
    assert co2 > 1.5, "Should reduce at least 1.5 tons CO2"
    assert co2 < 5.0, "Should be reasonable amount"
    
    print(f"  ✓ CO2 reduction: {co2:.2f} tons/year")
    return True


def run_all_tests():
    """Run all savings calculation tests."""
    print("=" * 60)
    print("Savings Calculations Validation Test")
    print("=" * 60)
    
    tests = [
        test_insulation_savings,
        test_hvac_upgrade_savings,
        test_window_upgrade_savings,
        test_appliance_savings,
        test_solar_savings,
        test_payback_roi,
        test_co2_reduction
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
