"""
Comprehensive Audit Report Generator
-------------------------------------
Generates professional-grade energy audit reports with implementation roadmaps.
"""

from datetime import datetime
from utility_rates import UtilityRates
from savings_calculator import SavingsCalculator, KBTU_TO_KWH


class AuditReport:
    """
    Generates comprehensive energy audit reports.
    """
    
    def __init__(self, profile, usage_data, recommendations, benchmarks=None, rates=None):
        """
        Initialize report generator.
        
        Args:
            profile: Home profile dictionary
            usage_data: Usage breakdown dictionary
            recommendations: List of recommendation dictionaries
            benchmarks: Benchmark data
            rates: UtilityRates instance
        """
        self.profile = profile
        self.usage_data = usage_data
        self.recommendations = recommendations
        self.benchmarks = benchmarks or {}
        self.rates = rates or UtilityRates()
        self.calculator = SavingsCalculator(regional_rates=self.rates)
    
    def generate_full_report(self):
        """
        Generate complete audit report with all sections.
        
        Returns:
            Complete report dictionary
        """
        total_kbtu = self.usage_data.get('total_kbtu', 0)
        sqft = self.profile.get('TOTSQFT_EN', 2000)
        eui = total_kbtu / sqft if sqft > 0 else 0
        
        # Calculate financial summary
        financial_summary = self._calculate_financial_summary()
        
        # Calculate projected usage
        projected_usage = self._calculate_projected_usage()
        
        # Generate implementation roadmap
        roadmap = self._generate_roadmap()
        
        # Calculate energy score
        energy_score = self._calculate_energy_score(eui)
        
        return {
            "status": "success",
            "audit_id": f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            
            "home_profile": self._format_home_profile(),
            
            "energy_score": energy_score,
            
            "current_usage": self._format_current_usage(),
            
            "usage_breakdown": self._format_usage_breakdown(),
            
            "benchmark_comparison": self._format_benchmark_comparison(eui),
            
            "recommendations": self.recommendations,
            
            "financial_summary": financial_summary,
            
            "projected_usage": projected_usage,
            
            "implementation_roadmap": roadmap
        }
    
    def _format_home_profile(self):
        """Format home profile section."""
        division = self.profile.get('DIVISION', 'Unknown')
        hdd = self.profile.get('HDD65', 5500)
        cdd = self.profile.get('CDD65', 800)
        
        return {
            "location": division,
            "type": self._get_home_type(),
            "size_sqft": int(self.profile.get('TOTSQFT_EN', 2000)),
            "year_built": self._parse_year(self.profile.get('YEARMADERANGE', '2000')),
            "occupants": int(self.profile.get('NHSLDMEM', 2)),
            "climate": {
                "hdd": int(hdd),
                "cdd": int(cdd)
            }
        }
    
    def _format_current_usage(self):
        """Format current usage section."""
        total_kbtu = self.usage_data.get('total_kbtu', 0)
        total_kwh = total_kbtu * KBTU_TO_KWH
        total_therms = total_kbtu * 0.01
        
        annual_cost = self.rates.kbtu_to_dollars(total_kbtu, 'blended')
        monthly_avg = annual_cost / 12
        
        sqft = self.profile.get('TOTSQFT_EN', 2000)
        eui = total_kbtu / sqft if sqft > 0 else 0
        
        co2_tons = self.calculator.calculate_co2_reduction(
            total_kwh, total_therms
        )
        
        return {
            "total_kbtu": round(total_kbtu),
            "total_kwh": round(total_kwh),
            "total_therms": round(total_therms),
            "annual_cost": round(annual_cost),
            "monthly_avg": round(monthly_avg),
            "eui": round(eui, 1),
            "carbon_tons": round(co2_tons, 2)
        }
    
    def _format_usage_breakdown(self):
        """Format usage breakdown by category."""
        total_kbtu = self.usage_data.get('total_kbtu', 1)
        
        heating_kbtu = self.usage_data.get('heating_kbtu', 0)
        cooling_kbtu = self.usage_data.get('cooling_kbtu', 0)
        water_kbtu = self.usage_data.get('water_kbtu', 0)
        baseload_kbtu = self.usage_data.get('baseload_kbtu', 0)
        
        # Estimate appliance and lighting from baseload
        appliance_kbtu = baseload_kbtu * 0.6
        lighting_kbtu = baseload_kbtu * 0.4
        other_kbtu = max(0, total_kbtu - heating_kbtu - cooling_kbtu - water_kbtu - baseload_kbtu)
        
        return {
            "heating": {
                "kbtu": round(heating_kbtu),
                "pct": round(heating_kbtu / total_kbtu * 100),
                "cost": round(self.rates.kbtu_to_dollars(heating_kbtu, 'gas'))
            },
            "cooling": {
                "kbtu": round(cooling_kbtu),
                "pct": round(cooling_kbtu / total_kbtu * 100),
                "cost": round(self.rates.kbtu_to_dollars(cooling_kbtu, 'elec'))
            },
            "water_heating": {
                "kbtu": round(water_kbtu),
                "pct": round(water_kbtu / total_kbtu * 100),
                "cost": round(self.rates.kbtu_to_dollars(water_kbtu, 'blended'))
            },
            "appliances": {
                "kbtu": round(appliance_kbtu),
                "pct": round(appliance_kbtu / total_kbtu * 100),
                "cost": round(self.rates.kbtu_to_dollars(appliance_kbtu, 'elec'))
            },
            "lighting": {
                "kbtu": round(lighting_kbtu),
                "pct": round(lighting_kbtu / total_kbtu * 100),
                "cost": round(self.rates.kbtu_to_dollars(lighting_kbtu, 'elec'))
            },
            "other": {
                "kbtu": round(other_kbtu),
                "pct": round(other_kbtu / total_kbtu * 100),
                "cost": round(self.rates.kbtu_to_dollars(other_kbtu, 'blended'))
            }
        }
    
    def _format_benchmark_comparison(self, eui):
        """Format benchmark comparison section."""
        division = self.profile.get('DIVISION', 'National')
        region_key = division.split()[0] if division else "National"
        
        # Get benchmark EUI
        target_eui = self.benchmarks.get('eui', {}).get(region_key, 35.0)
        similar_avg = target_eui * 1.1  # Assume 10% above target
        
        # Calculate percentile (simplified)
        if eui < target_eui * 0.7:
            percentile = 85
            rank = "15th percentile"
        elif eui < target_eui:
            percentile = 60
            rank = "40th percentile"
        elif eui < similar_avg:
            percentile = 45
            rank = "55th percentile"
        else:
            percentile = 25
            rank = "75th percentile"
        
        improvement_potential = ((eui - target_eui) / eui * 100) if eui > 0 else 0
        
        return {
            "similar_homes_avg": round(similar_avg * self.profile.get('TOTSQFT_EN', 2000)),
            "energy_star_target": round(target_eui * self.profile.get('TOTSQFT_EN', 2000)),
            "net_zero_target": round(15 * self.profile.get('TOTSQFT_EN', 2000)),  # 15 kBTU/sqft
            "your_rank": rank,
            "improvement_potential": f"{round(improvement_potential)}% below average"
        }
    
    def _calculate_energy_score(self, eui):
        """Calculate overall energy efficiency score."""
        division = self.profile.get('DIVISION', 'National')
        region_key = division.split()[0] if division else "National"
        target_eui = self.benchmarks.get('eui', {}).get(region_key, 35.0)
        
        # Score calculation: 100 - (ratio - 0.5) * 50
        ratio = eui / (target_eui + 0.1)
        raw_score = 100 - ((ratio - 0.5) * 50)
        score = max(0, min(100, raw_score))
        
        # Grade assignment
        if score >= 90:
            grade = "A+"
            label = "Excellent - Top Performer"
        elif score >= 80:
            grade = "A"
            label = "Excellent"
        elif score >= 70:
            grade = "B+"
            label = "Good - Above Average"
        elif score >= 60:
            grade = "B"
            label = "Good"
        elif score >= 50:
            grade = "C+"
            label = "Average - Some Improvement Potential"
        elif score >= 40:
            grade = "C"
            label = "Average - Significant Improvement Potential"
        elif score >= 30:
            grade = "D"
            label = "Below Average - Major Improvements Needed"
        else:
            grade = "F"
            label = "Poor - Urgent Action Required"
        
        percentile = int(score)
        
        return {
            "overall": int(score),
            "grade": grade,
            "percentile": percentile,
            "label": label
        }
    
    def _calculate_financial_summary(self):
        """Calculate financial summary across all recommendations."""
        total_investment = sum(r.get('cost', {}).get('estimate', 0) for r in self.recommendations)
        total_annual_savings = sum(r.get('savings', {}).get('annual_dollars', 0) for r in self.recommendations)
        total_lifetime_savings = sum(r.get('savings', {}).get('lifetime_dollars', 0) for r in self.recommendations)
        
        # Calculate average payback
        paybacks = [r.get('financial', {}).get('payback_years', 999) for r in self.recommendations if r.get('financial', {}).get('payback_years', 999) < 999]
        avg_payback = sum(paybacks) / len(paybacks) if paybacks else 0
        
        # Estimate rebates
        available_rebates = total_investment * 0.15  # Assume 15% average rebate
        net_investment = total_investment - available_rebates
        
        return {
            "total_investment": round(total_investment),
            "total_annual_savings": round(total_annual_savings),
            "total_lifetime_savings": round(total_lifetime_savings),
            "average_payback": round(avg_payback, 1),
            "available_rebates": round(available_rebates),
            "net_investment": round(net_investment)
        }
    
    def _calculate_projected_usage(self):
        """Calculate projected usage after implementing recommendations."""
        current_total = self.usage_data.get('total_kbtu', 0)
        current_cost = self.rates.kbtu_to_dollars(current_total, 'blended')
        
        # Sum all savings
        total_savings_kbtu = sum(
            r.get('savings', {}).get('annual_btu', 0) / 1000.0  # Convert BTU to kBTU
            for r in self.recommendations
        )
        
        # Quick wins (payback < 1 year)
        quick_wins_savings = sum(
            r.get('savings', {}).get('annual_btu', 0) / 1000.0
            for r in self.recommendations
            if r.get('financial', {}).get('payback_years', 999) < 1
        )
        
        after_all_kbtu = max(0, current_total - total_savings_kbtu)
        after_quick_wins_kbtu = max(0, current_total - quick_wins_savings)
        
        after_all_cost = self.rates.kbtu_to_dollars(after_all_kbtu, 'blended')
        after_quick_wins_cost = self.rates.kbtu_to_dollars(after_quick_wins_kbtu, 'blended')
        
        sqft = self.profile.get('TOTSQFT_EN', 2000)
        after_all_eui = after_all_kbtu / sqft if sqft > 0 else 0
        
        # Calculate new grade
        division = self.profile.get('DIVISION', 'National')
        region_key = division.split()[0] if division else "National"
        target_eui = self.benchmarks.get('eui', {}).get(region_key, 35.0)
        ratio = after_all_eui / (target_eui + 0.1)
        new_score = max(0, min(100, 100 - ((ratio - 0.5) * 50)))
        
        if new_score >= 90:
            new_grade = "A+"
        elif new_score >= 80:
            new_grade = "A-"
        elif new_score >= 70:
            new_grade = "B+"
        elif new_score >= 60:
            new_grade = "B"
        else:
            new_grade = "C+"
        
        reduction_pct = ((current_total - after_all_kbtu) / current_total * 100) if current_total > 0 else 0
        quick_wins_reduction = ((current_total - after_quick_wins_kbtu) / current_total * 100) if current_total > 0 else 0
        
        after_all_co2 = self.calculator.calculate_co2_reduction(
            after_all_kbtu * KBTU_TO_KWH, after_all_kbtu * 0.01
        )
        
        return {
            "after_all_recommendations": {
                "total_kbtu": round(after_all_kbtu),
                "annual_cost": round(after_all_cost),
                "reduction_pct": round(reduction_pct),
                "new_grade": new_grade,
                "carbon_tons": round(after_all_co2, 2)
            },
            "after_quick_wins": {
                "total_kbtu": round(after_quick_wins_kbtu),
                "annual_cost": round(after_quick_wins_cost),
                "reduction_pct": round(quick_wins_reduction)
            }
        }
    
    def _generate_roadmap(self):
        """Generate implementation roadmap by phase."""
        # Phase 1: Quick wins (< 1 year payback)
        phase_1 = [r for r in self.recommendations if r.get('financial', {}).get('payback_years', 999) < 1]
        
        # Phase 2: Short-term (1-5 years payback)
        phase_2 = [r for r in self.recommendations if 1 <= r.get('financial', {}).get('payback_years', 999) < 5]
        
        # Phase 3: Medium-term (5+ years payback)
        phase_3 = [r for r in self.recommendations if r.get('financial', {}).get('payback_years', 999) >= 5]
        
        def phase_summary(recs, timeline):
            cost = sum(r.get('cost', {}).get('estimate', 0) for r in recs)
            savings = sum(r.get('savings', {}).get('annual_dollars', 0) for r in recs)
            items = [r.get('title', '') for r in recs[:5]]  # Top 5 items
            
            return {
                "timeline": timeline,
                "cost": round(cost),
                "savings": round(savings),
                "items": items
            }
        
        return {
            "phase_1_immediate": phase_summary(phase_1, "0-3 months"),
            "phase_2_short_term": phase_summary(phase_2, "3-12 months"),
            "phase_3_medium_term": phase_summary(phase_3, "1-3 years")
        }
    
    def _get_home_type(self):
        """Get human-readable home type."""
        type_map = {
            '1': 'Mobile Home',
            '2': 'Single Family Detached',
            '3': 'Single Family Attached',
            '4': 'Apartment in 2-4 Unit Building',
            '5': 'Apartment in 5+ Unit Building'
        }
        return type_map.get(str(self.profile.get('TYPEHUQ', '2')), 'Single Family Detached')
    
    def _parse_year(self, year_str):
        """Parse year from YEARMADERANGE."""
        try:
            if isinstance(year_str, (int, float)):
                return int(year_str)
            year_map = {1: 1940, 2: 1955, 3: 1965, 4: 1975, 5: 1985, 6: 1995, 7: 2005, 8: 2018}
            if year_str in year_map:
                return year_map[year_str]
            return int(year_str) if str(year_str).isdigit() else 2000
        except:
            return 2000
