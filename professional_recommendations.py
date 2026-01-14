"""
Professional-Grade Recommendations
----------------------------------
Generates detailed, actionable recommendations with implementation guidance.
Quality level suitable for paid professional reports.
"""

from savings_calculator import SavingsCalculator
from utility_rates import UtilityRates


class ProfessionalRecommendationGenerator:
    """
    Generates professional-grade recommendations with detailed implementation steps.
    """
    
    def __init__(self, calculator, rates):
        self.calculator = calculator
        self.rates = rates
    
    def create_professional_recommendation(self, 
                                         title,
                                         category,
                                         priority,
                                         description,
                                         current_condition,
                                         recommended_action,
                                         savings_data,
                                         cost_estimate,
                                         financial,
                                         co2_reduction,
                                         implementation_steps=None,
                                         contractor_guidance=None,
                                         rebates=None,
                                         maintenance_schedule=None,
                                         warranty_info=None,
                                         difficulty_level=None,
                                         estimated_time=None,
                                         seasonal_timing=None,
                                         roi_analysis=None):
        """
        Create a comprehensive, professional-grade recommendation.
        """
        
        # Determine difficulty and time if not provided
        if difficulty_level is None:
            difficulty_level = self._estimate_difficulty(category, cost_estimate)
        
        if estimated_time is None:
            estimated_time = self._estimate_time(category, difficulty_level)
        
        # Generate implementation steps if not provided
        if implementation_steps is None:
            implementation_steps = self._generate_implementation_steps(
                category, difficulty_level
            )
        
        # Generate contractor guidance if not provided
        if contractor_guidance is None:
            contractor_guidance = self._generate_contractor_guidance(
                category, difficulty_level, cost_estimate
            )
        
        # Generate ROI analysis
        if roi_analysis is None:
            roi_analysis = self._generate_roi_analysis(
                financial, savings_data, cost_estimate
            )
        
        # Generate maintenance schedule if not provided
        if maintenance_schedule is None:
            maintenance_schedule = self._generate_maintenance_schedule(category)
        
        recommendation = {
            "id": f"rec_{category.lower().replace(' ', '_')}_{hash(title) % 10000}",
            "category": category,
            "priority": priority,
            "title": title,
            "description": description,
            "current_condition": current_condition,
            "recommended_action": recommended_action,
            
            # Implementation Details
            "implementation": {
                "difficulty": difficulty_level,
                "estimated_time": estimated_time,
                "seasonal_timing": seasonal_timing or self._recommend_timing(category),
                "steps": implementation_steps,
                "contractor_guidance": contractor_guidance
            },
            
            # Financial Details
            "cost": {
                "low": round(cost_estimate * 0.8),
                "mid": round(cost_estimate),
                "high": round(cost_estimate * 1.2),
                "estimate": round(cost_estimate),
                "financing_options": self._generate_financing_options(cost_estimate)
            },
            
            "savings": {
                "annual_btu": round(savings_data.get('annual_kbtu', 0) * 1000),
                "annual_kwh": round(savings_data.get('annual_kwh', 0)),
                "annual_therms": round(savings_data.get('annual_therms', 0)),
                "annual_dollars": round(savings_data.get('annual_dollars', 0)),
                "lifetime_dollars": round(savings_data.get('lifetime_dollars', 0)),
                "lifetime_years": savings_data.get('lifetime_years', 20)
            },
            
            "financial": {
                "payback_years": round(financial.get('payback_years', 0), 1),
                "roi_percent": round(financial.get('roi_percent', 0), 1),
                "npv": round(financial.get('npv', 0)),
                "roi_analysis": roi_analysis
            },
            
            "environmental": {
                "co2_reduction_tons": round(co2_reduction, 2),
                "co2_reduction_lifetime": round(co2_reduction * savings_data.get('lifetime_years', 20), 2),
                "equivalent_trees_planted": round(co2_reduction * 40, 0)  # ~40 trees per ton CO2
            },
            
            "incentives": {
                "rebates": rebates or [],
                "tax_credits": self._get_tax_credits(category),
                "utility_programs": self._get_utility_programs(category)
            },
            
            "warranty": warranty_info or self._get_default_warranty(category),
            "maintenance": maintenance_schedule,
            
            # Professional Details
            "professional_notes": {
                "code_requirements": self._get_code_requirements(category),
                "permits_required": self._requires_permit(category, cost_estimate),
                "inspection_required": self._requires_inspection(category),
                "energy_rating": self._get_energy_rating(category)
            },
            
            "next_steps": self._generate_next_steps(category, priority)
        }
        
        return recommendation
    
    def _estimate_difficulty(self, category, cost):
        """Estimate implementation difficulty."""
        if cost < 500:
            return "DIY - Easy"
        elif cost < 2000:
            return "DIY to Professional"
        elif cost < 10000:
            return "Professional Installation Recommended"
        else:
            return "Professional Installation Required"
    
    def _estimate_time(self, category, difficulty):
        """Estimate implementation time."""
        time_map = {
            "DIY - Easy": "2-4 hours",
            "DIY to Professional": "4-8 hours",
            "Professional Installation Recommended": "1-2 days",
            "Professional Installation Required": "2-5 days"
        }
        return time_map.get(difficulty, "1-2 days")
    
    def _generate_implementation_steps(self, category, difficulty):
        """Generate detailed implementation steps."""
        steps = {
            "Building Envelope": [
                "1. Schedule energy audit to identify specific problem areas",
                "2. Obtain quotes from 2-3 licensed contractors",
                "3. Check local building codes and permit requirements",
                "4. Schedule installation during optimal season (spring/fall)",
                "5. Ensure proper ventilation and moisture control",
                "6. Verify installation meets ENERGY STAR standards",
                "7. Schedule post-installation inspection"
            ],
            "Heating System": [
                "1. Get Manual J load calculation for proper sizing",
                "2. Obtain quotes from HVAC contractors (minimum 3)",
                "3. Verify contractor licensing and insurance",
                "4. Check for available rebates and incentives",
                "5. Schedule installation before heating season",
                "6. Ensure proper ductwork inspection and sealing",
                "7. Test system efficiency after installation",
                "8. Register warranty and schedule maintenance"
            ],
            "Cooling System": [
                "1. Get Manual J load calculation for proper AC sizing",
                "2. Evaluate SEER ratings (16+ recommended)",
                "3. Obtain quotes from certified HVAC contractors",
                "4. Check ductwork condition and insulation",
                "5. Schedule installation before cooling season",
                "6. Verify proper refrigerant charge",
                "7. Test system performance and efficiency"
            ],
            "Water Heating": [
                "1. Determine hot water usage patterns",
                "2. Calculate required capacity (gallons per minute)",
                "3. Evaluate fuel type options (gas vs electric vs heat pump)",
                "4. Check electrical/plumbing requirements",
                "5. Obtain quotes from licensed plumbers",
                "6. Verify local code compliance",
                "7. Schedule installation",
                "8. Test water temperature and flow rate"
            ],
            "Lighting": [
                "1. Audit all light fixtures in home",
                "2. Calculate total bulb count and wattage",
                "3. Purchase ENERGY STAR certified LED bulbs",
                "4. Replace bulbs starting with highest-use areas",
                "5. Consider smart lighting controls",
                "6. Dispose of old bulbs properly (recycling)"
            ]
        }
        
        return steps.get(category, [
            "1. Research product options and reviews",
            "2. Obtain professional quotes if needed",
            "3. Verify compatibility with existing systems",
            "4. Schedule installation",
            "5. Test and verify performance"
        ])
    
    def _generate_contractor_guidance(self, category, difficulty, cost):
        """Generate contractor selection guidance."""
        if "DIY" in difficulty:
            return {
                "contractor_required": False,
                "tips": [
                    "Watch installation videos and read manufacturer instructions",
                    "Ensure you have proper tools and safety equipment",
                    "Start with a small area to test your technique"
                ]
            }
        
        return {
            "contractor_required": True,
            "qualifications": self._get_required_qualifications(category),
            "selection_tips": [
                "Get at least 3 detailed quotes",
                "Verify contractor is licensed, bonded, and insured",
                "Check references and online reviews",
                "Ensure contractor is certified for specific equipment (e.g., NATE for HVAC)",
                "Verify warranty coverage and service availability",
                "Get everything in writing with detailed scope of work"
            ],
            "red_flags": [
                "Pressure to sign immediately",
                "Unusually low price (may indicate poor quality)",
                "No written contract or warranty",
                "Request for full payment upfront",
                "No insurance or licensing verification"
            ],
            "typical_cost_range": f"${cost * 0.8:,.0f} - ${cost * 1.2:,.0f}"
        }
    
    def _get_required_qualifications(self, category):
        """Get required contractor qualifications."""
        quals = {
            "Heating System": ["HVAC License", "NATE Certification", "EPA Refrigerant Certification"],
            "Cooling System": ["HVAC License", "NATE Certification", "EPA Refrigerant Certification"],
            "Water Heating": ["Plumbing License", "Electrical License (if applicable)"],
            "Building Envelope": ["General Contractor License", "Insulation Certification"],
            "Renewable Energy": ["Solar Installer Certification", "Electrical License", "NABCEP Certification"]
        }
        return quals.get(category, ["General Contractor License"])
    
    def _generate_roi_analysis(self, financial, savings_data, cost):
        """Generate detailed ROI analysis."""
        payback = financial.get('payback_years', 0)
        roi = financial.get('roi_percent', 0)
        annual_savings = savings_data.get('annual_dollars', 0)
        
        analysis = {
            "summary": f"Payback in {payback:.1f} years with {roi:.1f}% ROI over 10 years",
            "year_by_year": []
        }
        
        # Calculate year-by-year savings
        cumulative_savings = 0
        for year in range(1, 11):
            cumulative_savings += annual_savings
            net_savings = cumulative_savings - cost
            analysis["year_by_year"].append({
                "year": year,
                "cumulative_savings": round(cumulative_savings),
                "net_savings": round(net_savings),
                "roi": round((net_savings / cost * 100) if cost > 0 else 0, 1)
            })
        
        # Break-even analysis
        if payback > 0:
            analysis["break_even"] = {
                "years": round(payback, 1),
                "months": round(payback * 12, 0),
                "total_investment_at_break_even": round(cost)
            }
        
        return analysis
    
    def _generate_maintenance_schedule(self, category):
        """Generate maintenance schedule."""
        schedules = {
            "Heating System": {
                "monthly": ["Change air filter", "Check thermostat settings"],
                "annually": ["Professional inspection and tune-up", "Clean burners and heat exchanger", "Check ductwork"],
                "every_5_years": ["Replace air filter housing if needed"]
            },
            "Cooling System": {
                "monthly": ["Change air filter", "Clean outdoor unit"],
                "annually": ["Professional inspection and service", "Clean coils", "Check refrigerant levels"],
                "seasonal": ["Cover outdoor unit in winter (if applicable)"]
            },
            "Water Heating": {
                "monthly": ["Check for leaks", "Test temperature and pressure relief valve"],
                "annually": ["Flush tank to remove sediment", "Inspect anode rod", "Check for corrosion"],
                "every_5_years": ["Consider replacement if efficiency declining"]
            },
            "Building Envelope": {
                "annually": ["Inspect insulation for settling or damage", "Check for air leaks", "Inspect windows and doors"],
                "every_5_years": ["Professional energy audit", "Re-seal as needed"]
            }
        }
        
        return schedules.get(category, {
            "annually": ["Professional inspection", "Performance verification"]
        })
    
    def _get_tax_credits(self, category):
        """Get available tax credits."""
        credits = {
            "Heating System": ["Federal: Up to $600 for high-efficiency furnaces", "State: Varies by location"],
            "Cooling System": ["Federal: Up to $500 for high-efficiency AC", "State: Varies by location"],
            "Renewable Energy": ["Federal: 30% ITC for solar systems", "State: Additional incentives vary"],
            "Water Heating": ["Federal: Up to $800 for heat pump water heaters", "State: Varies"],
            "Building Envelope": ["Federal: Up to $500 for insulation and air sealing", "State: Varies"]
        }
        return credits.get(category, ["Check Energy.gov for current federal incentives"])
    
    def _get_utility_programs(self, category):
        """Get utility program information."""
        return [
            "Contact your local utility for rebate programs",
            "Check for time-of-use rate options",
            "Ask about energy efficiency programs",
            "Inquire about home energy assessments"
        ]
    
    def _get_default_warranty(self, category):
        """Get default warranty information."""
        warranties = {
            "Heating System": "10-20 years parts, 1-5 years labor (varies by manufacturer)",
            "Cooling System": "10-12 years parts, 1-5 years labor",
            "Water Heating": "6-12 years tank, 1-3 years parts",
            "Building Envelope": "Lifetime for materials, 1-5 years installation",
            "Renewable Energy": "25 years performance, 10-12 years equipment"
        }
        return warranties.get(category, "Varies by manufacturer and installer")
    
    def _get_code_requirements(self, category):
        """Get code requirements."""
        return {
            "Heating System": "Must meet local building codes, ASHRAE standards, and manufacturer specifications",
            "Cooling System": "Must meet local codes, EPA refrigerant regulations, and SEER minimums",
            "Water Heating": "Must meet plumbing codes, pressure vessel regulations, and safety standards",
            "Building Envelope": "Must meet local building codes and energy efficiency standards (IECC)"
        }.get(category, "Must meet all applicable local building codes")
    
    def _requires_permit(self, category, cost):
        """Determine if permit is required."""
        if cost > 5000:
            return True
        if category in ["Heating System", "Cooling System", "Renewable Energy"]:
            return True
        return False
    
    def _requires_inspection(self, category):
        """Determine if inspection is required."""
        return category in ["Heating System", "Cooling System", "Water Heating", "Renewable Energy"]
    
    def _get_energy_rating(self, category):
        """Get energy rating information."""
        ratings = {
            "Heating System": "Look for ENERGY STAR label, AFUE rating 90%+",
            "Cooling System": "Look for ENERGY STAR label, SEER rating 16+",
            "Water Heating": "Look for ENERGY STAR label, EF rating 2.0+ for heat pump",
            "Building Envelope": "Look for ENERGY STAR windows, R-value ratings for insulation"
        }
        return ratings.get(category, "Check for ENERGY STAR certification")
    
    def _recommend_timing(self, category):
        """Recommend optimal timing for installation."""
        timing = {
            "Heating System": "Fall (before heating season) for best pricing and availability",
            "Cooling System": "Spring (before cooling season) for best pricing and availability",
            "Water Heating": "Anytime, but avoid peak seasons for better pricing",
            "Building Envelope": "Spring or Fall (moderate weather) for comfort during installation",
            "Renewable Energy": "Spring/Summer for maximum solar production"
        }
        return timing.get(category, "Schedule during moderate weather for best conditions")
    
    def _generate_financing_options(self, cost):
        """Generate financing options."""
        options = []
        
        if cost < 1000:
            options.append("Pay with cash or credit card")
        elif cost < 5000:
            options.extend([
                "Home improvement credit card (0% APR promotions available)",
                "Personal loan",
                "Utility company financing programs"
            ])
        else:
            options.extend([
                "Home equity loan or HELOC (typically lowest rates)",
                "Energy-efficient mortgage (EEM)",
                "PACE financing (if available in your area)",
                "Utility company financing programs",
                "Manufacturer financing (for equipment purchases)"
            ])
        
        return options
    
    def _generate_next_steps(self, category, priority):
        """Generate actionable next steps."""
        steps = []
        
        if priority == "High":
            steps.append("Schedule consultation within 1-2 weeks")
            steps.append("Get quotes from 2-3 contractors")
        else:
            steps.append("Research options and plan for next 1-3 months")
            steps.append("Get quotes when ready to proceed")
        
        steps.extend([
            "Check available rebates and incentives",
            "Verify contractor credentials and references",
            "Review financing options if needed",
            "Schedule installation during optimal season"
        ])
        
        return steps
