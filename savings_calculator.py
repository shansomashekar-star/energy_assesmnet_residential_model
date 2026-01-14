"""
Physics-Based Energy Savings Calculator
----------------------------------------
Implements detailed savings calculations for various energy efficiency measures.
Uses physics-based models for accurate predictions.
"""

import numpy as np
from utility_rates import UtilityRates, KBTU_TO_KWH, KBTU_TO_THERM, THERM_TO_KWH


class SavingsCalculator:
    """
    Calculates energy savings using physics-based models.
    """
    
    def __init__(self, regional_rates=None, climate_data=None):
        """
        Initialize calculator.
        
        Args:
            regional_rates: UtilityRates instance or dict with division
            climate_data: Dict with 'hdd' (heating degree days) and 'cdd' (cooling degree days)
        """
        if isinstance(regional_rates, dict):
            self.rates = UtilityRates(**regional_rates)
        elif regional_rates is None:
            self.rates = UtilityRates()
        else:
            self.rates = regional_rates
        
        self.climate_data = climate_data or {'hdd': 5500, 'cdd': 800}
        self.hdd = self.climate_data.get('hdd', 5500)
        self.cdd = self.climate_data.get('cdd', 800)
        
        # Equipment efficiency curves and degradation factors
        self.equipment_lifespans = {
            'furnace': 20,
            'boiler': 25,
            'heat_pump': 15,
            'ac': 15,
            'water_heater': 12,
            'refrigerator': 15,
            'dishwasher': 12,
            'washer': 12,
            'dryer': 12,
            'windows': 25,
            'insulation': 50,
            'solar_pv': 25
        }
    
    def calculate_insulation_savings(self, current_r_value, new_r_value, sqft, 
                                     surface_type='attic', heating_fuel='gas'):
        """
        Calculate insulation upgrade savings.
        
        Formula: Heat loss = (Area × ΔT × 24 × days) / R-value
        Savings = (Heat_loss_old - Heat_loss_new) × fuel_cost
        
        Args:
            current_r_value: Current R-value
            new_r_value: New R-value after upgrade
            sqft: Square footage of insulated area
            surface_type: 'attic', 'wall', 'floor', 'basement'
            heating_fuel: 'gas', 'elec', 'propane', 'fuel_oil'
        
        Returns:
            Dict with annual savings in kBTU, kWh, therms, and dollars
        """
        if current_r_value >= new_r_value:
            return self._zero_savings()
        
        # Heat loss formula: Q = (A × ΔT × 24 × days) / R
        # For annual: Q = (A × HDD × 24) / R (simplified)
        # ΔT is embedded in HDD
        
        # Base heat loss calculation (kBTU)
        # Typical indoor temp: 70°F, base temp: 65°F
        # HDD already accounts for temperature difference
        
        # Heat loss coefficient (kBTU per sqft per HDD per R-value)
        # Simplified: 1 kBTU/sqft/HDD per R-value unit
        heat_loss_old = (sqft * self.hdd) / (current_r_value + 0.1)  # Avoid div by zero
        heat_loss_new = (sqft * self.hdd) / (new_r_value + 0.1)
        
        annual_kbtu_savings = heat_loss_old - heat_loss_new
        
        # Convert to other units
        annual_kwh = annual_kbtu_savings * KBTU_TO_KWH
        annual_therms = annual_kbtu_savings * KBTU_TO_THERM
        
        # Calculate dollar savings
        annual_dollars = self.rates.kbtu_to_dollars(annual_kbtu_savings, heating_fuel)
        
        return {
            'annual_kbtu': max(0, annual_kbtu_savings),
            'annual_kwh': max(0, annual_kwh),
            'annual_therms': max(0, annual_therms),
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': self.equipment_lifespans.get('insulation', 50)
        }
    
    def calculate_hvac_upgrade_savings(self, old_efficiency, new_efficiency,
                                       heating_load_kbtu, fuel_type='gas'):
        """
        Calculate HVAC system upgrade savings.
        
        Formula: Energy input = Output / Efficiency
        Savings = Load × (1/old_eff - 1/new_eff) × fuel_cost
        
        Args:
            old_efficiency: Current efficiency (AFUE for heating, SEER for cooling)
            new_efficiency: New efficiency
            heating_load_kbtu: Annual heating load in kBTU
            fuel_type: 'gas', 'elec', 'propane', 'fuel_oil'
        
        Returns:
            Dict with annual savings
        """
        if old_efficiency >= new_efficiency or old_efficiency <= 0:
            return self._zero_savings()
        
        # Convert efficiency percentages to decimals
        old_eff = old_efficiency / 100.0 if old_efficiency > 1 else old_efficiency
        new_eff = new_efficiency / 100.0 if new_efficiency > 1 else new_efficiency
        
        # Energy input = Output / Efficiency
        old_input = heating_load_kbtu / old_eff
        new_input = heating_load_kbtu / new_eff
        
        annual_kbtu_savings = old_input - new_input
        
        annual_kwh = annual_kbtu_savings * KBTU_TO_KWH
        annual_therms = annual_kbtu_savings * KBTU_TO_THERM
        annual_dollars = self.rates.kbtu_to_dollars(annual_kbtu_savings, fuel_type)
        
        equipment_type = 'furnace' if fuel_type == 'gas' else 'heat_pump'
        lifetime = self.equipment_lifespans.get(equipment_type, 20)
        
        return {
            'annual_kbtu': max(0, annual_kbtu_savings),
            'annual_kwh': max(0, annual_kwh),
            'annual_therms': max(0, annual_therms),
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': lifetime
        }
    
    def calculate_cooling_upgrade_savings(self, old_seer, new_seer, cooling_load_kbtu):
        """
        Calculate AC/heat pump cooling upgrade savings.
        
        Args:
            old_seer: Current SEER rating
            new_seer: New SEER rating
            cooling_load_kbtu: Annual cooling load in kBTU
        """
        if old_seer >= new_seer or old_seer <= 0:
            return self._zero_savings()
        
        # SEER = Cooling output (BTU) / Energy input (Wh)
        # Energy input = Output / SEER
        old_input_kwh = (cooling_load_kbtu * 1000) / old_seer  # Convert kBTU to BTU
        new_input_kwh = (cooling_load_kbtu * 1000) / new_seer
        
        annual_kwh_savings = old_input_kwh - new_input_kwh
        annual_kbtu_savings = annual_kwh_savings / KBTU_TO_KWH
        annual_dollars = annual_kwh_savings * self.rates.get_electricity_rate()
        
        return {
            'annual_kbtu': max(0, annual_kbtu_savings),
            'annual_kwh': max(0, annual_kwh_savings),
            'annual_therms': 0,
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': self.equipment_lifespans.get('ac', 15)
        }
    
    def calculate_window_upgrade_savings(self, old_u_factor, new_u_factor,
                                         window_sqft, hdd=None, cdd=None):
        """
        Calculate window replacement savings.
        
        U-factor measures heat loss (lower is better).
        Formula: Heat loss = U × Area × ΔT × hours
        
        Args:
            old_u_factor: Current U-factor
            new_u_factor: New U-factor
            window_sqft: Total window area in sqft
            hdd: Heating degree days (optional, uses instance default if None)
            cdd: Cooling degree days (optional, uses instance default if None)
        """
        if old_u_factor <= new_u_factor or old_u_factor <= 0:
            return self._zero_savings()
        
        hdd = hdd or self.hdd
        cdd = cdd or self.cdd
        
        # Heating savings: U-factor reduction × area × HDD × 24 hours
        # Simplified: 1 U-factor unit = ~1 kBTU/sqft/HDD
        heating_savings_kbtu = (old_u_factor - new_u_factor) * window_sqft * hdd * 0.024
        
        # Cooling savings: Similar calculation for cooling season
        # SHGC (Solar Heat Gain Coefficient) also matters, but simplified here
        cooling_savings_kbtu = (old_u_factor - new_u_factor) * window_sqft * cdd * 0.018
        
        total_kbtu_savings = heating_savings_kbtu + cooling_savings_kbtu
        annual_kwh = total_kbtu_savings * KBTU_TO_KWH
        
        # Assume 60% heating (gas), 40% cooling (electric)
        heating_dollars = self.rates.kbtu_to_dollars(heating_savings_kbtu, 'gas')
        cooling_dollars = annual_kwh * 0.4 * self.rates.get_electricity_rate()
        annual_dollars = heating_dollars + cooling_dollars
        
        return {
            'annual_kbtu': max(0, total_kbtu_savings),
            'annual_kwh': max(0, annual_kwh),
            'annual_therms': max(0, heating_savings_kbtu * KBTU_TO_THERM),
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': self.equipment_lifespans.get('windows', 25)
        }
    
    def calculate_appliance_savings(self, old_kwh_year, new_kwh_year):
        """
        Calculate appliance upgrade savings.
        
        Args:
            old_kwh_year: Current annual kWh usage
            new_kwh_year: New annual kWh usage
        """
        annual_kwh_savings = old_kwh_year - new_kwh_year
        annual_kbtu_savings = annual_kwh_savings / KBTU_TO_KWH
        annual_dollars = annual_kwh_savings * self.rates.get_electricity_rate()
        
        return {
            'annual_kbtu': max(0, annual_kbtu_savings),
            'annual_kwh': max(0, annual_kwh_savings),
            'annual_therms': 0,
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': self.equipment_lifespans.get('refrigerator', 15)
        }
    
    def calculate_water_heater_savings(self, old_efficiency, new_efficiency,
                                      water_heating_kbtu, fuel_type='gas'):
        """
        Calculate water heater upgrade savings.
        
        Args:
            old_efficiency: Current EF (Energy Factor) or efficiency %
            new_efficiency: New EF or efficiency %
            water_heating_kbtu: Annual water heating load in kBTU
            fuel_type: 'gas', 'elec', 'propane', 'fuel_oil'
        """
        if old_efficiency >= new_efficiency or old_efficiency <= 0:
            return self._zero_savings()
        
        # EF is output/input, so input = output / EF
        old_eff = old_efficiency / 100.0 if old_efficiency > 1 else old_efficiency
        new_eff = new_efficiency / 100.0 if new_efficiency > 1 else new_efficiency
        
        old_input = water_heating_kbtu / old_eff
        new_input = water_heating_kbtu / new_eff
        
        annual_kbtu_savings = old_input - new_input
        annual_kwh = annual_kbtu_savings * KBTU_TO_KWH
        annual_therms = annual_kbtu_savings * KBTU_TO_THERM
        annual_dollars = self.rates.kbtu_to_dollars(annual_kbtu_savings, fuel_type)
        
        return {
            'annual_kbtu': max(0, annual_kbtu_savings),
            'annual_kwh': max(0, annual_kwh),
            'annual_therms': max(0, annual_therms),
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': self.equipment_lifespans.get('water_heater', 12)
        }
    
    def calculate_solar_savings(self, system_size_kw, location=None,
                               roof_orientation='south', shading_factor=1.0):
        """
        Calculate solar PV system savings.
        
        Formula: Production = Size × Sun Hours × Efficiency × Shading
        
        Args:
            system_size_kw: System size in kW
            location: Optional location for sun hours (uses default if None)
            roof_orientation: 'south', 'east', 'west', 'north'
            shading_factor: 0.0 to 1.0 (1.0 = no shading)
        """
        # Average annual sun hours by region (kWh per kW installed)
        sun_hours_by_region = {
            'Northeast': 1200,
            'Midwest': 1400,
            'South': 1600,
            'West': 1800,
            'default': 1500
        }
        
        region = self.rates.region
        base_sun_hours = sun_hours_by_region.get(region, sun_hours_by_region['default'])
        
        # Orientation factor
        orientation_factors = {
            'south': 1.0,
            'east': 0.85,
            'west': 0.85,
            'north': 0.60
        }
        orientation_factor = orientation_factors.get(roof_orientation.lower(), 1.0)
        
        # System efficiency (accounting for inverter losses, etc.)
        system_efficiency = 0.85
        
        # Annual production in kWh
        annual_kwh = system_size_kw * base_sun_hours * orientation_factor * shading_factor * system_efficiency
        annual_kbtu = annual_kwh / KBTU_TO_KWH
        annual_dollars = annual_kwh * self.rates.get_electricity_rate()
        
        return {
            'annual_kbtu': max(0, annual_kbtu),
            'annual_kwh': max(0, annual_kwh),
            'annual_therms': 0,
            'annual_dollars': max(0, annual_dollars),
            'lifetime_years': self.equipment_lifespans.get('solar_pv', 25)
        }
    
    def calculate_lifetime_savings(self, annual_savings_dollars, equipment_life_years, discount_rate=0.03):
        """
        Calculate lifetime savings with NPV (Net Present Value).
        
        Args:
            annual_savings_dollars: Annual dollar savings
            equipment_life_years: Expected equipment lifetime
            discount_rate: Discount rate for NPV (default 3%)
        
        Returns:
            Dict with lifetime savings, NPV, and simple payback
        """
        if annual_savings_dollars <= 0:
            return {
                'lifetime_dollars': 0,
                'npv': 0,
                'simple_payback_years': float('inf')
            }
        
        # Simple lifetime savings (no discounting)
        lifetime_dollars = annual_savings_dollars * equipment_life_years
        
        # NPV calculation
        npv = sum(
            annual_savings_dollars / ((1 + discount_rate) ** year)
            for year in range(1, equipment_life_years + 1)
        )
        
        return {
            'lifetime_dollars': lifetime_dollars,
            'npv': npv,
            'simple_payback_years': equipment_life_years  # Will be calculated separately with cost
        }
    
    def calculate_payback_roi(self, upfront_cost, annual_savings_dollars, rebates=0):
        """
        Calculate payback period and ROI.
        
        Args:
            upfront_cost: Total installation cost
            annual_savings_dollars: Annual dollar savings
            rebates: Available rebates/incentives
        
        Returns:
            Dict with payback period and ROI
        """
        net_cost = upfront_cost - rebates
        
        if annual_savings_dollars <= 0:
            return {
                'payback_years': float('inf'),
                'roi_percent': 0
            }
        
        payback_years = net_cost / annual_savings_dollars
        
        # ROI over 10 years (standard period)
        roi_percent = ((annual_savings_dollars * 10) - net_cost) / net_cost * 100 if net_cost > 0 else 0
        
        return {
            'payback_years': payback_years,
            'roi_percent': roi_percent
        }
    
    def calculate_co2_reduction(self, annual_kwh_savings, annual_therm_savings=0):
        """
        Calculate CO2 reduction from energy savings.
        
        Args:
            annual_kwh_savings: Annual kWh savings
            annual_therm_savings: Annual therm savings (gas)
        
        Returns:
            CO2 reduction in tons per year
        """
        # CO2 emissions factors (lbs per unit)
        # US grid average: ~0.85 lbs CO2 per kWh
        # Natural gas: ~11.7 lbs CO2 per therm
        co2_per_kwh = 0.85  # lbs
        co2_per_therm = 11.7  # lbs
        
        total_co2_lbs = (annual_kwh_savings * co2_per_kwh) + (annual_therm_savings * co2_per_therm)
        co2_tons = total_co2_lbs / 2000.0  # Convert to tons
        
        return max(0, co2_tons)
    
    def _zero_savings(self):
        """Return zero savings structure."""
        return {
            'annual_kbtu': 0,
            'annual_kwh': 0,
            'annual_therms': 0,
            'annual_dollars': 0,
            'lifetime_years': 0
        }
