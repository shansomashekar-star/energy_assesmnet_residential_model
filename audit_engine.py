"""
Enhanced Audit Engine: Comprehensive Expert System for Home Energy Recommendations
-----------------------------------------------------------------------------------
Implements detailed logical rules with physics-based savings calculations.
Expanded from 5 to 15+ recommendation categories.
"""

from savings_calculator import SavingsCalculator
from utility_rates import UtilityRates
from professional_recommendations import ProfessionalRecommendationGenerator


class AuditEngine:
    def __init__(self, benchmarks=None, rates=None, climate_data=None):
        """
        Initialize audit engine.
        
        Args:
            benchmarks: Benchmark data dict
            rates: UtilityRates instance or dict for initialization
            climate_data: Dict with 'hdd' and 'cdd'
        """
        self.benchmarks = benchmarks or {}
        
        # Initialize rates
        if isinstance(rates, dict):
            self.rates = UtilityRates(**rates)
        elif rates is None:
            self.rates = UtilityRates()
        else:
            self.rates = rates
        
        # Initialize savings calculator
        calc_kwargs = {}
        if climate_data:
            calc_kwargs['climate_data'] = climate_data
        if isinstance(rates, dict):
            calc_kwargs['regional_rates'] = rates
        elif rates:
            calc_kwargs['regional_rates'] = rates
        
        self.calculator = SavingsCalculator(**calc_kwargs)
        self.professional_gen = ProfessionalRecommendationGenerator(self.calculator, self.rates)
        
        # Initialize savings calculator
        calc_kwargs = {}
        if climate_data:
            calc_kwargs['climate_data'] = climate_data
        if isinstance(rates, dict):
            calc_kwargs['regional_rates'] = rates
        elif rates:
            calc_kwargs['regional_rates'] = rates
        
        self.calculator = SavingsCalculator(**calc_kwargs)
    
    def generate_recommendations(self, profile, usage_breakdown, total_kbtu):
        """
        Main entry point. Returns comprehensive list of recommendations.
        """
        recs = []
        
        # 1. Building Envelope Recommendations
        recs.extend(self._analyze_building_envelope(profile, usage_breakdown, total_kbtu))
        
        # 2. Heating System Recommendations
        recs.extend(self._analyze_heating_system(profile, usage_breakdown, total_kbtu))
        
        # 3. Cooling System Recommendations
        recs.extend(self._analyze_cooling_system(profile, usage_breakdown, total_kbtu))
        
        # 4. Water Heating Recommendations
        recs.extend(self._analyze_water_heating(profile, usage_breakdown))
        
        # 5. Appliance Recommendations
        recs.extend(self._analyze_appliances(profile, usage_breakdown))
        
        # 6. Lighting Recommendations
        recs.extend(self._analyze_lighting(profile, usage_breakdown))
        
        # 7. Renewable Energy Recommendations
        recs.extend(self._analyze_renewable_energy(profile, total_kbtu))
        
        # 8. Smart Home Technology
        recs.extend(self._analyze_smart_home(profile, usage_breakdown))
        
        # 9. Behavioral Recommendations
        recs.extend(self._analyze_behavioral(profile, usage_breakdown, total_kbtu))
        
        # Sort by payback period (ascending)
        return sorted(recs, key=lambda x: x.get('financial', {}).get('payback_years', 999))
    
    def _analyze_building_envelope(self, profile, breakdown, total):
        """Building envelope recommendations: insulation, windows, air sealing."""
        recs = []
        heat_kbtu = breakdown.get('heating_kbtu', 0)
        cool_kbtu = breakdown.get('cooling_kbtu', 0)
        sqft = profile.get('TOTSQFT_EN', 2000)
        
        # 1. Attic Insulation Upgrade
        adq_insul = self._safe_int(profile.get('ADQINSUL', '2'))
        attic = profile.get('ATTIC', '1')
        if adq_insul >= 2 and attic in ['1', '2'] and heat_kbtu > 20000:
            # Estimate current R-value based on insulation adequacy
            current_r = 19 if adq_insul == 2 else 10  # Adequate vs Poor
            new_r = 49  # R-49 recommended for attics
            attic_sqft = sqft * 0.9  # Approximate attic area
            
            savings_data = self.calculator.calculate_insulation_savings(
                current_r, new_r, attic_sqft, 'attic', 'gas'
            )
            
            if savings_data['annual_dollars'] > 100:
                cost_estimate = 2500 + (attic_sqft - 1000) * 1.5  # $1.50/sqft
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=500
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], savings_data['annual_therms']
                )
                
                # Use professional recommendation generator
                rec = self.professional_gen.create_professional_recommendation(
                    title="Upgrade Attic Insulation to R-49",
                    category="Building Envelope",
                    priority="High" if financial['payback_years'] < 5 else "Medium",
                    description="Your attic insulation is below recommended levels. Upgrading to R-49 can significantly reduce heating costs by minimizing heat loss through the roof, which accounts for up to 25% of total heat loss in many homes.",
                    current_condition=f"Current R-value: ~{current_r} (estimated). Recommended: R-49 for your climate zone.",
                    recommended_action="Add blown-in cellulose or fiberglass insulation to achieve R-49, ensuring proper ventilation to prevent moisture issues.",
                    savings_data=savings_data,
                    cost_estimate=cost_estimate,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: $500", "Utility Rebate: $200-500"],
                    seasonal_timing="Spring or Fall for comfortable working conditions"
                )
                recs.append(rec)
        
        # 2. Wall Insulation
        walltype = profile.get('WALLTYPE', '1')
        year_built = self._parse_year(profile.get('YEARMADERANGE', '2000'))
        if year_built < 1980 and heat_kbtu > 30000:
            savings_data = self.calculator.calculate_insulation_savings(
                5, 15, sqft * 2.5, 'wall', 'gas'  # Assume 2.5x sqft for wall area
            )
            if savings_data['annual_dollars'] > 200:
                cost_estimate = 8000 + (sqft - 1500) * 3.0
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=1000
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], savings_data['annual_therms']
                )
                
                recs.append(self._create_recommendation(
                    id="rec_envelope_002",
                    category="Building Envelope",
                    title="Add Wall Insulation",
                    description="Older homes often lack wall insulation. Adding insulation can reduce heat loss through walls.",
                    current_condition="Walls likely uninsulated or minimally insulated",
                    recommended_action="Blow-in insulation or exterior insulation",
                    difficulty="Professional Installation Required",
                    installation_time="3-5 days",
                    cost_low=6000, cost_mid=cost_estimate, cost_high=cost_estimate + 3000,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    priority="Medium"
                ))
        
        # 3. Window Replacement
        windows = self._safe_int(profile.get('WINDOWS', '3'))
        typeglass = profile.get('TYPEGLASS', '1')
        if windows >= 3 and (heat_kbtu > 25000 or cool_kbtu > 15000):
            # Estimate window area (15% of floor area typical)
            window_sqft = sqft * 0.15
            old_u = 1.2 if typeglass in ['1', '2'] else 0.5  # Single/double vs triple
            new_u = 0.30  # Modern double-pane low-e
            
            savings_data = self.calculator.calculate_window_upgrade_savings(
                old_u, new_u, window_sqft
            )
            
            if savings_data['annual_dollars'] > 150:
                cost_estimate = window_sqft * 400  # $400/sqft for windows
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=500
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], savings_data['annual_therms']
                )
                
                recs.append(self._create_recommendation(
                    id="rec_envelope_003",
                    category="Building Envelope",
                    title="Replace Windows with Energy-Efficient Models",
                    description="Upgrading to double or triple-pane low-e windows reduces heat loss and solar heat gain.",
                    current_condition=f"Single-pane or older double-pane windows (U-factor ~{old_u})",
                    recommended_action="Install ENERGY STAR certified windows with U-factor < 0.30",
                    difficulty="Professional Installation Required",
                    installation_time="3-7 days",
                    cost_low=cost_estimate * 0.8, cost_mid=cost_estimate, cost_high=cost_estimate * 1.2,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: $500", "ENERGY STAR Rebate: $200-400"],
                    priority="Medium" if financial['payback_years'] < 15 else "Low"
                ))
        
        # 4. Air Sealing
        drafty = self._safe_int(profile.get('DRAFTY', '3'))
        if drafty >= 2 and (heat_kbtu > 20000 or cool_kbtu > 10000):
            # Air sealing saves 10-20% of heating/cooling
            savings_kbtu = (heat_kbtu + cool_kbtu) * 0.15
            savings_data = {
                'annual_kbtu': savings_kbtu,
                'annual_kwh': savings_kbtu * 0.293,
                'annual_therms': savings_kbtu * 0.01,
                'annual_dollars': self.rates.kbtu_to_dollars(savings_kbtu, 'blended'),
                'lifetime_years': 20
            }
            
            if savings_data['annual_dollars'] > 50:
                cost_estimate = 400 + (sqft - 1000) * 0.3
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars']
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], savings_data['annual_therms']
                )
                
                recs.append(self._create_recommendation(
                    id="rec_envelope_004",
                    category="Building Envelope",
                    title="Air Sealing & Weatherstripping",
                    description="Seal gaps around windows, doors, and penetrations to reduce air infiltration.",
                    current_condition="Noticeable drafts and air leaks",
                    recommended_action="Caulk, weatherstrip, and seal all gaps",
                    difficulty="DIY to Professional",
                    installation_time="1-2 days",
                    cost_low=300, cost_mid=cost_estimate, cost_high=cost_estimate + 200,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    priority="High" if financial['payback_years'] < 2 else "Medium"
                ))
        
        return recs
    
    def _analyze_heating_system(self, profile, breakdown, total):
        """Heating system recommendations: furnace, boiler, heat pump upgrades."""
        recs = []
        heat_kbtu = breakdown.get('heating_kbtu', 0)
        equipm = profile.get('EQUIPM', '3')  # 3 = Furnace
        fuel_heat = profile.get('FUELHEAT', '1')  # 1 = Natural Gas
        
        # Estimate equipment age and efficiency
        acequipage = self._safe_int(profile.get('ACEQUIPAGE', '3'))
        # Age categories: 1=new, 2=1-5yr, 3=6-10yr, 4=11-15yr, 5=16-20yr, 6=20+yr
        age_years = {1: 2, 2: 3, 3: 8, 4: 13, 5: 18, 6: 25}.get(acequipage, 10)
        
        if age_years > 15 and heat_kbtu > 30000:
            # Old furnace efficiency: 60-78% AFUE
            old_afue = max(60, 95 - age_years * 1.5)
            new_afue = 95  # High-efficiency furnace
            
            savings_data = self.calculator.calculate_hvac_upgrade_savings(
                old_afue, new_afue, heat_kbtu, 'gas'
            )
            
            if savings_data['annual_dollars'] > 200:
                sqft = profile.get('TOTSQFT_EN', 2000)
                cost_estimate = 3500 + (sqft - 1500) * 1.5
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=600
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], savings_data['annual_therms']
                )
                
                recs.append(self._create_recommendation(
                    id="rec_heating_001",
                    category="Heating System",
                    title=f"Upgrade to {new_afue}% AFUE Furnace",
                    description=f"Your {age_years}-year-old furnace has an estimated efficiency of {old_afue}% AFUE. A modern {new_afue}% AFUE furnace would significantly reduce heating costs.",
                    current_condition=f"{age_years}-year-old natural gas furnace, ~{old_afue}% AFUE",
                    recommended_action="Install ENERGY STAR certified 95% AFUE gas furnace with variable-speed blower",
                    difficulty="Professional Installation Required",
                    installation_time="1-2 days",
                    cost_low=3500, cost_mid=cost_estimate, cost_high=cost_estimate + 2000,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: $600", "State Rebate: $500", "Utility Rebate: $400"],
                    priority="High" if financial['payback_years'] < 5 else "Medium"
                ))
        
        # Programmable/Smart Thermostat
        protherm = profile.get('PROTHERM', '0')
        if protherm == '0' and heat_kbtu > 20000:
            # Programmable thermostat saves 5-10%
            savings_kbtu = heat_kbtu * 0.08
            savings_data = {
                'annual_kbtu': savings_kbtu,
                'annual_kwh': savings_kbtu * 0.293,
                'annual_therms': savings_kbtu * 0.01,
                'annual_dollars': self.rates.kbtu_to_dollars(savings_kbtu, 'gas'),
                'lifetime_years': 10
            }
            
            cost_estimate = 250  # Smart thermostat
            financial = self.calculator.calculate_payback_roi(
                cost_estimate, savings_data['annual_dollars']
            )
            co2 = self.calculator.calculate_co2_reduction(
                savings_data['annual_kwh'], savings_data['annual_therms']
            )
            
            recs.append(self._create_recommendation(
                id="rec_heating_002",
                category="Heating System",
                title="Install Smart Thermostat",
                description="A programmable or smart thermostat can automatically adjust temperatures when you're away, saving energy without sacrificing comfort.",
                current_condition="Manual or non-programmable thermostat",
                recommended_action="Install Wi-Fi enabled smart thermostat with scheduling",
                difficulty="DIY",
                installation_time="1-2 hours",
                cost_low=150, cost_mid=250, cost_high=350,
                savings_data=savings_data,
                financial=financial,
                co2_reduction=co2,
                priority="High" if financial['payback_years'] < 2 else "Medium"
            ))
        
        return recs
    
    def _analyze_cooling_system(self, profile, breakdown, total):
        """Cooling system recommendations: AC, heat pump, ventilation."""
        recs = []
        cool_kbtu = breakdown.get('cooling_kbtu', 0)
        acequipm = profile.get('ACEQUIPM_PUB', '1')
        acequipage = self._safe_int(profile.get('ACEQUIPAGE', '3'))
        
        # AC replacement
        age_years = {1: 2, 2: 3, 3: 8, 4: 13, 5: 18, 6: 25}.get(acequipage, 10)
        if age_years > 12 and cool_kbtu > 10000:
            old_seer = max(8, 16 - age_years * 0.5)  # Older units have lower SEER
            new_seer = 18  # High-efficiency AC
            
            savings_data = self.calculator.calculate_cooling_upgrade_savings(
                old_seer, new_seer, cool_kbtu
            )
            
            if savings_data['annual_dollars'] > 150:
                sqft = profile.get('TOTSQFT_EN', 2000)
                cost_estimate = 4000 + (sqft - 1500) * 2.0
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=500
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], 0
                )
                
                recs.append(self._create_recommendation(
                    id="rec_cooling_001",
                    category="Cooling System",
                    title=f"Upgrade to SEER {new_seer} Air Conditioner",
                    description=f"Your {age_years}-year-old AC unit has an estimated SEER of {old_seer:.1f}. A modern SEER {new_seer} unit uses significantly less energy.",
                    current_condition=f"{age_years}-year-old AC, ~{old_seer:.1f} SEER",
                    recommended_action="Install ENERGY STAR certified SEER 18+ central AC",
                    difficulty="Professional Installation Required",
                    installation_time="1-2 days",
                    cost_low=3500, cost_mid=cost_estimate, cost_high=cost_estimate + 2000,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: $500", "Utility Rebate: $300-500"],
                    priority="Medium"
                ))
        
        return recs
    
    def _analyze_water_heating(self, profile, breakdown):
        """Water heating recommendations: heat pump, tankless, solar."""
        recs = []
        wh_kbtu = breakdown.get('water_kbtu', 0)
        fuel_h2o = profile.get('FUELH2O', '1')
        wheatage = self._safe_int(profile.get('WHEATAGE', '3'))
        
        # Heat Pump Water Heater (for electric)
        if fuel_h2o == '1' and wh_kbtu > 10000:  # Electric and high usage
            old_ef = 0.90  # Standard electric resistance
            new_ef = 2.50  # Heat pump water heater EF
            
            savings_data = self.calculator.calculate_water_heater_savings(
                old_ef, new_ef, wh_kbtu, 'elec'
            )
            
            if savings_data['annual_dollars'] > 100:
                cost_estimate = 2500
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=800
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], 0
                )
                
                recs.append(self._create_recommendation(
                    id="rec_water_001",
                    category="Water Heating",
                    title="Install Heat Pump Water Heater",
                    description="Heat pump water heaters use 60-70% less energy than standard electric resistance units by extracting heat from the air.",
                    current_condition="Standard electric resistance water heater",
                    recommended_action="Install ENERGY STAR certified heat pump water heater",
                    difficulty="Professional Installation Required",
                    installation_time="4-6 hours",
                    cost_low=2000, cost_mid=2500, cost_high=3000,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: $800", "Utility Rebate: $300-500"],
                    priority="High" if financial['payback_years'] < 4 else "Medium"
                ))
        
        # Tankless Water Heater (for gas)
        if fuel_h2o in ['2', '3'] and wh_kbtu > 12000:  # Gas or propane
            old_ef = 0.60  # Standard gas tank
            new_ef = 0.95  # Tankless gas
            
            savings_data = self.calculator.calculate_water_heater_savings(
                old_ef, new_ef, wh_kbtu, 'gas'
            )
            
            if savings_data['annual_dollars'] > 150:
                cost_estimate = 3000
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=500
                )
                co2 = self.calculator.calculate_co2_reduction(
                    savings_data['annual_kwh'], savings_data['annual_therms']
                )
                
                recs.append(self._create_recommendation(
                    id="rec_water_002",
                    category="Water Heating",
                    title="Install Tankless Water Heater",
                    description="Tankless water heaters heat water on-demand, eliminating standby losses and providing endless hot water.",
                    current_condition="Standard gas storage water heater",
                    recommended_action="Install ENERGY STAR certified tankless gas water heater",
                    difficulty="Professional Installation Required",
                    installation_time="4-6 hours",
                    cost_low=2500, cost_mid=3000, cost_high=4000,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: $500", "Utility Rebate: $200-400"],
                    priority="Medium"
                ))
        
        return recs
    
    def _analyze_appliances(self, profile, breakdown):
        """Appliance recommendations: ENERGY STAR upgrades."""
        recs = []
        base_kbtu = breakdown.get('baseload_kbtu', 0)
        
        # Refrigerator upgrade
        num_frig = self._safe_int(profile.get('NUMFRIG', 1))
        age_frig = self._safe_int(profile.get('AGERFRI1', 3))
        if (num_frig > 1 or age_frig >= 4) and base_kbtu > 5000:
            # Old fridge: 600-800 kWh/year, New ENERGY STAR: 300-400 kWh/year
            old_kwh = 700
            new_kwh = 350
            
            savings_data = self.calculator.calculate_appliance_savings(old_kwh, new_kwh)
            
            if savings_data['annual_dollars'] > 50:
                cost_estimate = 800 if num_frig > 1 else 1200  # Remove 2nd vs upgrade
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars']
                )
                co2 = self.calculator.calculate_co2_reduction(savings_data['annual_kwh'], 0)
                
                recs.append(self._create_recommendation(
                    id="rec_appliance_001",
                    category="Appliances",
                    title="Upgrade to ENERGY STAR Refrigerator" if num_frig == 1 else "Remove or Upgrade Second Refrigerator",
                    description="Older refrigerators consume 2-3x more energy than modern ENERGY STAR models.",
                    current_condition=f"{'Second' if num_frig > 1 else 'Old'} refrigerator, high energy consumption",
                    recommended_action="Replace with ENERGY STAR certified refrigerator or remove second unit",
                    difficulty="DIY",
                    installation_time="2-4 hours",
                    cost_low=600, cost_mid=cost_estimate, cost_high=cost_estimate + 400,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    priority="Medium"
                ))
        
        return recs
    
    def _analyze_lighting(self, profile, breakdown):
        """Lighting recommendations: LED conversion, smart controls."""
        recs = []
        lgtinled = self._safe_int(profile.get('LGTINLED', '2'))
        lgtincan = self._safe_int(profile.get('LGTINCAN', '3'))
        
        # LED conversion
        if lgtincan >= 2:  # Significant incandescent usage
            # Assume 30 bulbs, 60W each, 4 hours/day = 2628 kWh/year
            # LED: 9W each = 394 kWh/year
            old_kwh = 2628
            new_kwh = 394
            
            savings_data = self.calculator.calculate_appliance_savings(old_kwh, new_kwh)
            
            if savings_data['annual_dollars'] > 100:
                cost_estimate = 30 * 5  # 30 bulbs × $5 each
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars']
                )
                co2 = self.calculator.calculate_co2_reduction(savings_data['annual_kwh'], 0)
                
                recs.append(self._create_recommendation(
                    id="rec_lighting_001",
                    category="Lighting",
                    title="Convert to LED Bulbs",
                    description="LED bulbs use 85% less energy than incandescent and last 25x longer.",
                    current_condition="Significant incandescent bulb usage",
                    recommended_action="Replace all incandescent bulbs with ENERGY STAR LED bulbs",
                    difficulty="DIY",
                    installation_time="2-4 hours",
                    cost_low=100, cost_mid=cost_estimate, cost_high=cost_estimate + 50,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    priority="High" if financial['payback_years'] < 1 else "Medium"
                ))
        
        return recs
    
    def _analyze_renewable_energy(self, profile, total_kbtu):
        """Renewable energy recommendations: solar PV, solar water heating."""
        recs = []
        
        # Solar PV
        sqft = profile.get('TOTSQFT_EN', 2000)
        if total_kbtu > 50000:  # High usage home
            # Size system to cover 80% of usage
            annual_kwh = total_kbtu * 0.293
            system_size_kw = (annual_kwh * 0.8) / 1500  # Assume 1500 kWh/kW/year
            
            savings_data = self.calculator.calculate_solar_savings(
                system_size_kw, roof_orientation='south', shading_factor=0.9
            )
            
            if savings_data['annual_dollars'] > 500:
                cost_estimate = system_size_kw * 3000  # $3/W installed
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars'], rebates=system_size_kw * 1000
                )
                co2 = self.calculator.calculate_co2_reduction(savings_data['annual_kwh'], 0)
                
                recs.append(self._create_recommendation(
                    id="rec_renewable_001",
                    category="Renewable Energy",
                    title=f"Install {system_size_kw:.1f}kW Solar PV System",
                    description=f"A {system_size_kw:.1f}kW solar system can offset most of your electricity usage and provide significant savings over 25+ years.",
                    current_condition="No solar generation",
                    recommended_action="Install grid-tied solar PV system with net metering",
                    difficulty="Professional Installation Required",
                    installation_time="2-5 days",
                    cost_low=cost_estimate * 0.9, cost_mid=cost_estimate, cost_high=cost_estimate * 1.1,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    rebates=["Federal Tax Credit: 30%", "State/Utility Rebates: Varies"],
                    priority="Medium" if financial['payback_years'] < 12 else "Low"
                ))
        
        return recs
    
    def _analyze_smart_home(self, profile, breakdown):
        """Smart home technology recommendations."""
        recs = []
        smartmeter = profile.get('SMARTMETER', '0')
        
        # Energy monitoring system
        if smartmeter == '0':
            savings_kbtu = breakdown.get('baseload_kbtu', 0) * 0.05  # 5% from awareness
            savings_data = {
                'annual_kbtu': savings_kbtu,
                'annual_kwh': savings_kbtu * 0.293,
                'annual_therms': 0,
                'annual_dollars': self.rates.kbtu_to_dollars(savings_kbtu, 'blended'),
                'lifetime_years': 10
            }
            
            if savings_data['annual_dollars'] > 50:
                cost_estimate = 200
                financial = self.calculator.calculate_payback_roi(
                    cost_estimate, savings_data['annual_dollars']
                )
                co2 = self.calculator.calculate_co2_reduction(savings_data['annual_kwh'], 0)
                
                recs.append(self._create_recommendation(
                    id="rec_smart_001",
                    category="Smart Home Technology",
                    title="Install Energy Monitoring System",
                    description="Real-time energy monitoring helps identify energy hogs and encourages conservation.",
                    current_condition="No energy monitoring",
                    recommended_action="Install whole-house energy monitor or smart plugs",
                    difficulty="DIY",
                    installation_time="1-2 hours",
                    cost_low=100, cost_mid=200, cost_high=300,
                    savings_data=savings_data,
                    financial=financial,
                    co2_reduction=co2,
                    priority="Low"
                ))
        
        return recs
    
    def _analyze_behavioral(self, profile, breakdown, total):
        """Behavioral recommendations: temperature settings, usage patterns."""
        recs = []
        
        # Temperature setback
        temphome = self._safe_int(profile.get('TEMPHOME', 70))
        if temphome > 72:  # High heating setpoint
            savings_kbtu = breakdown.get('heating_kbtu', 0) * 0.05  # 5% per degree
            savings_data = {
                'annual_kbtu': savings_kbtu,
                'annual_kwh': savings_kbtu * 0.293,
                'annual_therms': savings_kbtu * 0.01,
                'annual_dollars': self.rates.kbtu_to_dollars(savings_kbtu, 'gas'),
                'lifetime_years': 1
            }
            
            if savings_data['annual_dollars'] > 30:
                recs.append(self._create_recommendation(
                    id="rec_behavioral_001",
                    category="Behavioral",
                    title="Optimize Temperature Settings",
                    description=f"Lowering your heating setpoint from {temphome}°F to 68°F can save energy without significant comfort loss.",
                    current_condition=f"Heating setpoint: {temphome}°F",
                    recommended_action="Set heating to 68°F when home, 62°F when away/sleeping",
                    difficulty="No Cost",
                    installation_time="Immediate",
                    cost_low=0, cost_mid=0, cost_high=0,
                    savings_data=savings_data,
                    financial={'payback_years': 0, 'roi_percent': float('inf')},
                    co2_reduction=self.calculator.calculate_co2_reduction(
                        savings_data['annual_kwh'], savings_data['annual_therms']
                    ),
                    priority="High"
                ))
        
        return recs
    
    def _create_recommendation(self, id, category, title, description, current_condition,
                              recommended_action, difficulty, installation_time,
                              cost_low, cost_mid, cost_high, savings_data, financial,
                              co2_reduction, rebates=None, priority="Medium", **kwargs):
        """Create a standardized recommendation dictionary."""
        lifetime_data = self.calculator.calculate_lifetime_savings(
            savings_data['annual_dollars'], savings_data['lifetime_years']
        )
        
        return {
            "id": id,
            "category": category,
            "priority": priority,
            "title": title,
            "description": description,
            "current_condition": current_condition,
            "recommended_action": recommended_action,
            "difficulty": difficulty,
            "installation_time": installation_time,
            "cost": {
                "low": round(cost_low),
                "mid": round(cost_mid),
                "high": round(cost_high),
                "estimate": round(cost_mid)
            },
            "savings": {
                "annual_btu": round(savings_data['annual_kbtu'] * 1000),  # Convert to BTU
                "annual_kwh": round(savings_data['annual_kwh']),
                "annual_therms": round(savings_data['annual_therms']),
                "annual_dollars": round(savings_data['annual_dollars']),
                "lifetime_dollars": round(lifetime_data['lifetime_dollars']),
                "lifetime_years": savings_data['lifetime_years']
            },
            "financial": {
                "payback_years": round(financial['payback_years'], 1),
                "roi_percent": round(financial['roi_percent'], 1),
                "npv": round(lifetime_data['npv'])
            },
            "environmental": {
                "co2_reduction_tons": round(co2_reduction, 2),
                "co2_reduction_lifetime": round(co2_reduction * savings_data['lifetime_years'], 2)
            },
            "rebates": rebates or [],
            "implementation_notes": f"Schedule installation during off-season for best pricing. Ensure proper sizing and professional installation for optimal performance.",
            "maintenance": "Follow manufacturer recommendations for maintenance schedule."
        }
    
    def _safe_int(self, value, default=0):
        """Safely convert to int."""
        try:
            if isinstance(value, str):
                return int(value)
            return int(value) if value is not None else default
        except:
            return default
    
    def _parse_year(self, year_str):
        """Parse year from YEARMADERANGE or similar."""
        try:
            if isinstance(year_str, (int, float)):
                return int(year_str)
            # YEARMADERANGE: 1=Before 1950, 2=1950-1959, ..., 8=2016-2020
            year_map = {1: 1940, 2: 1955, 3: 1965, 4: 1975, 5: 1985, 6: 1995, 7: 2005, 8: 2018}
            if year_str in year_map:
                return year_map[year_str]
            return int(year_str) if str(year_str).isdigit() else 2000
        except:
            return 2000
