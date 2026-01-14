"""
Regional Utility Rate Database
-------------------------------
Provides state and division-level average electricity and gas rates.
Based on EIA (Energy Information Administration) data.
"""

# Regional utility rates (2020-2024 averages)
# Electricity rates in $/kWh
ELECTRICITY_RATES = {
    # By Census Division
    "Northeast": {
        "New England": 0.22,
        "Middle Atlantic": 0.16,
        "default": 0.19
    },
    "Midwest": {
        "East North Central": 0.13,
        "West North Central": 0.12,
        "default": 0.125
    },
    "South": {
        "South Atlantic": 0.12,
        "East South Central": 0.11,
        "West South Central": 0.11,
        "default": 0.113
    },
    "West": {
        "Mountain": 0.12,
        "Pacific": 0.18,
        "default": 0.15
    },
    "default": 0.14  # National average
}

# Natural gas rates in $/Therm (1 Therm = 29.3 kWh)
GAS_RATES = {
    "Northeast": {
        "New England": 1.80,
        "Middle Atlantic": 1.20,
        "default": 1.50
    },
    "Midwest": {
        "East North Central": 1.00,
        "West North Central": 0.90,
        "default": 0.95
    },
    "South": {
        "South Atlantic": 1.10,
        "East South Central": 1.00,
        "West South Central": 0.85,
        "default": 0.98
    },
    "West": {
        "Mountain": 0.95,
        "Pacific": 1.40,
        "default": 1.18
    },
    "default": 1.20  # National average
}

# Propane rates in $/gallon (1 gallon ≈ 91,000 BTU ≈ 0.91 Therms)
PROPANE_RATES = {
    "Northeast": 2.80,
    "Midwest": 2.20,
    "South": 2.10,
    "West": 2.50,
    "default": 2.40
}

# Fuel oil rates in $/gallon (1 gallon ≈ 138,000 BTU ≈ 1.38 Therms)
FUEL_OIL_RATES = {
    "Northeast": 3.20,
    "Midwest": 3.00,
    "South": 3.10,
    "West": 3.30,
    "default": 3.15
}

# Conversion factors
KBTU_TO_KWH = 0.293
KBTU_TO_THERM = 0.01  # 1 kBTU = 0.01 Therms (100 kBTU = 1 Therm)
THERM_TO_KWH = 29.3


class UtilityRates:
    """Manages regional utility rates for energy cost calculations."""
    
    def __init__(self, division=None, state=None, custom_rates=None):
        """
        Initialize utility rates.
        
        Args:
            division: Census division name (e.g., "Northeast", "South")
            state: State name (optional, for more precise rates)
            custom_rates: Dict with 'elec' and/or 'gas' rates to override defaults
        """
        self.division = division or "default"
        self.state = state
        self.custom_rates = custom_rates or {}
        
        # Determine region
        if division:
            # Extract base region from division
            if "Northeast" in division or "New England" in division or "Middle Atlantic" in division:
                self.region = "Northeast"
            elif "Midwest" in division or "North Central" in division:
                self.region = "Midwest"
            elif "South" in division:
                self.region = "South"
            elif "West" in division or "Mountain" in division or "Pacific" in division:
                self.region = "West"
            else:
                self.region = "default"
        else:
            self.region = "default"
    
    def get_electricity_rate(self):
        """Get electricity rate in $/kWh."""
        if 'elec' in self.custom_rates:
            return self.custom_rates['elec']
        
        region_rates = ELECTRICITY_RATES.get(self.region, ELECTRICITY_RATES["default"])
        if isinstance(region_rates, dict):
            # Try to find division-specific rate
            if self.division and self.division in region_rates:
                return region_rates[self.division]
            return region_rates.get("default", ELECTRICITY_RATES["default"])
        return region_rates
    
    def get_gas_rate(self):
        """Get natural gas rate in $/Therm."""
        if 'gas' in self.custom_rates:
            return self.custom_rates['gas']
        
        region_rates = GAS_RATES.get(self.region, GAS_RATES["default"])
        if isinstance(region_rates, dict):
            if self.division and self.division in region_rates:
                return region_rates[self.division]
            return region_rates.get("default", GAS_RATES["default"])
        return region_rates
    
    def get_propane_rate(self):
        """Get propane rate in $/gallon."""
        if 'propane' in self.custom_rates:
            return self.custom_rates['propane']
        return PROPANE_RATES.get(self.region, PROPANE_RATES["default"])
    
    def get_fuel_oil_rate(self):
        """Get fuel oil rate in $/gallon."""
        if 'fuel_oil' in self.custom_rates:
            return self.custom_rates['fuel_oil']
        return FUEL_OIL_RATES.get(self.region, FUEL_OIL_RATES["default"])
    
    def kbtu_to_dollars(self, kbtu, fuel_type='blended'):
        """
        Convert kBTU to dollars based on fuel type.
        
        Args:
            kbtu: Energy in kBTU
            fuel_type: 'elec', 'gas', 'propane', 'fuel_oil', or 'blended'
        
        Returns:
            Cost in dollars
        """
        if fuel_type == 'elec':
            kwh = kbtu * KBTU_TO_KWH
            return kwh * self.get_electricity_rate()
        elif fuel_type == 'gas':
            therms = kbtu * KBTU_TO_THERM
            return therms * self.get_gas_rate()
        elif fuel_type == 'propane':
            # 1 gallon propane ≈ 91 kBTU
            gallons = kbtu / 91.0
            return gallons * self.get_propane_rate()
        elif fuel_type == 'fuel_oil':
            # 1 gallon fuel oil ≈ 138 kBTU
            gallons = kbtu / 138.0
            return gallons * self.get_fuel_oil_rate()
        else:  # blended
            # Assume 60% gas, 40% electric for blended
            gas_cost = self.kbtu_to_dollars(kbtu * 0.6, 'gas')
            elec_cost = self.kbtu_to_dollars(kbtu * 0.4, 'elec')
            return gas_cost + elec_cost
    
    def get_all_rates(self):
        """Get all rates as a dictionary."""
        return {
            'electricity': self.get_electricity_rate(),
            'gas': self.get_gas_rate(),
            'propane': self.get_propane_rate(),
            'fuel_oil': self.get_fuel_oil_rate(),
            'region': self.region,
            'division': self.division
        }


def get_rates_for_division(division, custom_rates=None):
    """Convenience function to get rates for a division."""
    return UtilityRates(division=division, custom_rates=custom_rates)
