"""
Google ADK Energy Analysis Tools
Tools for TOU (Time of Use) plan analysis and energy efficiency recommendations
Updated to use all available data OR last 365 days, whichever is smaller
"""

import json
import pandas as pd
from typing import Dict, Any, Optional

# Import configuration and existing SQL tools
from .config import config
from shared_tools.simple_sql_agents import execute_query_json_tool


def analyze_tou_plan_fit(customer_id: str, analysis_days: int = 365) -> str:
    """
    ADK Tool: Analyze customer's fit for 8PM-8AM TOU (Time of Use) plan
    
    This tool analyzes a customer's energy usage pattern using all available data
    OR the last 365 days (whichever is smaller) to determine if they would benefit 
    from a Time of Use plan where nighttime (8PM-8AM) usage is free and
    daytime (8AM-8PM) usage costs twice the normal rate.
    
    Args:
        customer_id: Customer ID to analyze (e.g., 'CUST000001')
        analysis_days: Maximum days to analyze (default: 365)
        
    Returns:
        JSON string with TOU plan fit analysis and recommendations
    """
    try:
        # SQL query to analyze TOU plan fit using all data OR last 365 days
        tou_analysis_sql = f"""
        WITH customer_date_range AS (
          SELECT 
            customer_id,
            MIN(date) as first_date,
            MAX(date) as last_date,
            DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as total_days_available
          FROM `{config.project_id}.{config.dataset_name}.smartmeter_data`
          WHERE customer_id = '{customer_id}'
            AND usage IS NOT NULL
            AND CAST(usage AS FLOAT64) >= 0
          GROUP BY customer_id
        ),
        analysis_period AS (
          SELECT 
            customer_id,
            first_date,
            last_date,
            total_days_available,
            -- Use either all data available OR last 365 days, whichever is smaller
            CASE 
              WHEN total_days_available <= {analysis_days} THEN first_date
              ELSE DATE_SUB(last_date, INTERVAL {analysis_days-1} DAY)
            END as analysis_start_date,
            CASE 
              WHEN total_days_available <= {analysis_days} THEN total_days_available
              ELSE {analysis_days}
            END as analysis_days_used
          FROM customer_date_range
        ),
        usage_analysis AS (
          SELECT 
            sm.customer_id,
            sm.date,
            -- Classify time periods (8PM-8AM = night, 8AM-8PM = day)
            CASE 
              WHEN CAST(sm.hour AS INT64) >= 20 OR CAST(sm.hour AS INT64) < 8 THEN 'night'
              ELSE 'day'
            END as time_period,
            SUM(CAST(sm.usage AS FLOAT64)) as period_usage,
            COUNT(*) as reading_count
          FROM `{config.project_id}.{config.dataset_name}.smartmeter_data` sm
          INNER JOIN analysis_period ap ON sm.customer_id = ap.customer_id
          WHERE sm.customer_id = '{customer_id}'
            AND sm.date >= ap.analysis_start_date
            AND sm.usage IS NOT NULL
            AND CAST(sm.usage AS FLOAT64) >= 0
          GROUP BY sm.customer_id, sm.date, time_period
        ),
        daily_summary AS (
          SELECT 
            ua.customer_id,
            ua.date,
            SUM(CASE WHEN ua.time_period = 'night' THEN ua.period_usage ELSE 0 END) as night_usage,
            SUM(CASE WHEN ua.time_period = 'day' THEN ua.period_usage ELSE 0 END) as day_usage,
            SUM(ua.period_usage) as total_daily_usage
          FROM usage_analysis ua
          GROUP BY ua.customer_id, ua.date
        ),
        overall_stats AS (
          SELECT 
            ds.customer_id,
            ap.analysis_days_used as analysis_days,
            ap.total_days_available as total_data_days,
            ap.analysis_start_date,
            ap.last_date as analysis_end_date,
            COUNT(DISTINCT ds.date) as actual_analysis_days,
            AVG(ds.night_usage) as avg_night_usage,
            AVG(ds.day_usage) as avg_day_usage,
            AVG(ds.total_daily_usage) as avg_daily_usage,
            SUM(ds.night_usage) / SUM(ds.total_daily_usage) * 100 as night_usage_percentage,
            SUM(ds.day_usage) / SUM(ds.total_daily_usage) * 100 as day_usage_percentage,
            STDDEV(ds.total_daily_usage) as usage_variability
          FROM daily_summary ds
          INNER JOIN analysis_period ap ON ds.customer_id = ap.customer_id
          GROUP BY ds.customer_id, ap.analysis_days_used, ap.total_days_available, ap.analysis_start_date, ap.last_date
        ),
        cost_comparison AS (
          SELECT 
            customer_id,
            analysis_days,
            actual_analysis_days,
            total_data_days,
            analysis_start_date,
            analysis_end_date,
            avg_night_usage,
            avg_day_usage,
            avg_daily_usage,
            night_usage_percentage,
            day_usage_percentage,
            usage_variability,
            
            -- Cost calculations (assuming base rate of $0.12/kWh)
            (avg_night_usage + avg_day_usage) * 0.12 as standard_plan_daily_cost,
            (avg_night_usage * 0.00 + avg_day_usage * 0.24) as tou_plan_daily_cost,
            
            -- Savings calculation
            ((avg_night_usage + avg_day_usage) * 0.12) - (avg_night_usage * 0.00 + avg_day_usage * 0.24) as daily_savings,
            
            -- Fit score based on night usage percentage
            CASE 
              WHEN night_usage_percentage >= 60 THEN 'Excellent'
              WHEN night_usage_percentage >= 45 THEN 'Good'
              WHEN night_usage_percentage >= 30 THEN 'Fair'
              ELSE 'Poor'
            END as tou_fit_rating
            
          FROM overall_stats
        )
        SELECT 
          customer_id,
          analysis_days,
          actual_analysis_days,
          total_data_days,
          analysis_start_date,
          analysis_end_date,
          ROUND(avg_night_usage, 3) as avg_night_usage_kwh,
          ROUND(avg_day_usage, 3) as avg_day_usage_kwh,
          ROUND(avg_daily_usage, 3) as avg_daily_usage_kwh,
          ROUND(night_usage_percentage, 1) as night_usage_percentage,
          ROUND(day_usage_percentage, 1) as day_usage_percentage,
          ROUND(standard_plan_daily_cost, 2) as standard_plan_daily_cost,
          ROUND(tou_plan_daily_cost, 2) as tou_plan_daily_cost,
          ROUND(daily_savings, 2) as daily_savings,
          ROUND(daily_savings * 365, 2) as annual_savings,
          ROUND(usage_variability, 3) as usage_variability,
          tou_fit_rating,
          
          -- Additional insights
          CASE 
            WHEN daily_savings > 0 THEN 'Recommended'
            WHEN daily_savings > -0.50 THEN 'Neutral'
            ELSE 'Not Recommended'
          END as recommendation,
          
          CASE 
            WHEN night_usage_percentage < 30 THEN 'Consider shifting high-energy activities (laundry, dishwasher, EV charging) to nighttime hours'
            WHEN night_usage_percentage < 45 THEN 'Good start! Try to shift more usage to nighttime when possible'
            ELSE 'Excellent usage pattern for TOU plan'
          END as optimization_tip
          
        FROM cost_comparison
        """
        
        # Execute the query using existing tool
        result = execute_query_json_tool(tou_analysis_sql)
        result_data = json.loads(result)
        
        if not result_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": "Failed to analyze TOU plan fit",
                "details": result_data.get("error", "Unknown error"),
                "customer_id": customer_id
            }, indent=2)
        
        # Extract analysis results
        if not result_data.get("data") or len(result_data["data"]) == 0:
            return json.dumps({
                "success": False,
                "error": "No data found for customer",
                "customer_id": customer_id,
                "suggestion": "Check if customer_id exists and has recent data"
            }, indent=2)
        
        analysis = result_data["data"][0]
        
        # Format the response with detailed insights
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "analysis_period_info": {
                "total_data_days_available": analysis["total_data_days"],
                "analysis_days_used": analysis["analysis_days"],
                "actual_analysis_days": analysis["actual_analysis_days"],
                "analysis_start_date": analysis["analysis_start_date"],
                "analysis_end_date": analysis["analysis_end_date"],
                "note": f"Used {'all available data' if analysis['total_data_days'] <= analysis_days else f'last {analysis_days} days'} for analysis"
            },
            "usage_pattern": {
                "avg_daily_usage_kwh": analysis["avg_daily_usage_kwh"],
                "avg_night_usage_kwh": analysis["avg_night_usage_kwh"],
                "avg_day_usage_kwh": analysis["avg_day_usage_kwh"],
                "night_usage_percentage": analysis["night_usage_percentage"],
                "day_usage_percentage": analysis["day_usage_percentage"],
                "usage_variability": analysis["usage_variability"]
            },
            "cost_analysis": {
                "standard_plan_daily_cost": analysis["standard_plan_daily_cost"],
                "tou_plan_daily_cost": analysis["tou_plan_daily_cost"],
                "daily_savings": analysis["daily_savings"],
                "annual_savings": analysis["annual_savings"]
            },
            "tou_plan_assessment": {
                "fit_rating": analysis["tou_fit_rating"],
                "recommendation": analysis["recommendation"],
                "optimization_tip": analysis["optimization_tip"]
            },
            "summary": f"Customer {customer_id} analysis based on {analysis['actual_analysis_days']} days of data "
                      f"({analysis['analysis_start_date']} to {analysis['analysis_end_date']}). "
                      f"Night usage: {analysis['night_usage_percentage']}%. "
                      f"TOU plan would {'save' if analysis['daily_savings'] > 0 else 'cost'} "
                      f"${abs(analysis['daily_savings']):.2f}/day (${abs(analysis['annual_savings']):.2f}/year). "
                      f"Rating: {analysis['tou_fit_rating']}"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error analyzing TOU plan fit: {str(e)}",
            "customer_id": customer_id
        }, indent=2)


def analyze_energy_efficiency(customer_id: str, analysis_days: int = 365) -> str:
    """
    Enhanced ADK Tool: Intelligent energy efficiency analysis with personalized recommendations
    
    This tool provides sophisticated analysis including:
    - Equipment degradation detection
    - Seasonal efficiency patterns
    - Usage trend analysis
    - Phantom load detection
    - Peak efficiency assessment
    - Personalized recommendations based on actual patterns
    
    Args:
        customer_id: Customer ID to analyze (e.g., 'CUST000001')
        analysis_days: Maximum days to analyze (default: 365)
        
    Returns:
        JSON string with comprehensive personalized energy efficiency analysis
    """
    try:
        # Enhanced SQL query with comprehensive efficiency analysis
        efficiency_analysis_sql = f"""
            WITH customer_date_range AS (
      SELECT 
        customer_id,
        MIN(date) as first_date,
        MAX(date) as last_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as total_days_available
      FROM `energyagentai.alberta_energy_ai.smartmeter_data`
      WHERE customer_id = '{customer_id}'
        AND usage IS NOT NULL
        AND CAST(usage AS FLOAT64) >= 0
      GROUP BY customer_id
    ),
    analysis_period AS (
      SELECT 
        customer_id,
        first_date,
        last_date,
        total_days_available,
        CASE 
          WHEN total_days_available <= {analysis_days} THEN first_date
          ELSE DATE_SUB(last_date, INTERVAL {analysis_days - 1} DAY)
        END as analysis_start_date,
        CASE 
          WHEN total_days_available <= {analysis_days} THEN total_days_available
          ELSE {analysis_days}
        END as analysis_days_used
      FROM customer_date_range
    ),
    daily_patterns AS (
      SELECT 
        sm.customer_id,
        sm.date,
        EXTRACT(MONTH FROM sm.date) as month,
        EXTRACT(DAYOFWEEK FROM sm.date) as day_of_week,
        SUM(CAST(sm.usage AS FLOAT64)) as daily_usage,
        MAX(CAST(sm.usage AS FLOAT64)) as peak_interval_usage,
        MIN(CAST(sm.usage AS FLOAT64)) as min_interval_usage,
        SUM(CASE WHEN CAST(sm.hour AS INT64) >= 20 OR CAST(sm.hour AS INT64) < 8 
                 THEN CAST(sm.usage AS FLOAT64) ELSE 0 END) as night_usage,
        SUM(CASE WHEN CAST(sm.hour AS INT64) >= 8 AND CAST(sm.hour AS INT64) < 20 
                 THEN CAST(sm.usage AS FLOAT64) ELSE 0 END) as day_usage,
        SUM(CASE WHEN CAST(sm.usage AS FLOAT64) > 2.0 THEN 1 ELSE 0 END) as high_usage_intervals,
        SUM(CASE WHEN sm.faulty_equipment IS NOT NULL AND sm.faulty_equipment != '' THEN 1 ELSE 0 END) as fault_intervals,
        COUNT(*) as total_intervals
      FROM `energyagentai.alberta_energy_ai.smartmeter_data` sm
      INNER JOIN analysis_period ap ON sm.customer_id = ap.customer_id
      WHERE sm.customer_id = '{customer_id}'
        AND sm.date >= ap.analysis_start_date
        AND sm.usage IS NOT NULL
        AND CAST(sm.usage AS FLOAT64) >= 0
      GROUP BY sm.customer_id, sm.date
    ),
    time_ranked_patterns AS (
      SELECT *,
             ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY date) AS rn,
             COUNT(*) OVER (PARTITION BY customer_id) AS total_rows
      FROM daily_patterns
    ),
    time_based_analysis AS (
      SELECT 
        customer_id,
        AVG(CASE WHEN rn <= total_rows * 0.3 THEN daily_usage END) as early_avg_usage,
        AVG(CASE WHEN rn <= total_rows * 0.3 THEN min_interval_usage END) as early_baseline,
        AVG(CASE WHEN rn > total_rows * 0.7 THEN daily_usage END) as late_avg_usage,
        AVG(CASE WHEN rn > total_rows * 0.7 THEN min_interval_usage END) as late_baseline,
        AVG(CASE WHEN month IN (12, 1, 2) THEN daily_usage END) as winter_usage,
        AVG(CASE WHEN month IN (6, 7, 8) THEN daily_usage END) as summer_usage,
        AVG(CASE WHEN month IN (3, 4, 5, 9, 10, 11) THEN daily_usage END) as mild_season_usage,
        COUNT(*) as total_days
      FROM time_ranked_patterns
      GROUP BY customer_id
    ),
    efficiency_metrics AS (
      SELECT 
        dp.customer_id,
        ap.analysis_days_used,
        ap.total_days_available,
        ap.analysis_start_date,
        ap.last_date as analysis_end_date,
        COUNT(DISTINCT dp.date) as actual_analysis_days,
        AVG(dp.daily_usage) as avg_daily_usage,
        STDDEV(dp.daily_usage) as daily_usage_stddev,
        MAX(dp.daily_usage) as max_daily_usage,
        MIN(dp.daily_usage) as min_daily_usage,
        AVG(dp.min_interval_usage) as avg_baseline_usage,
        STDDEV(dp.min_interval_usage) as baseline_variability,
        AVG(dp.peak_interval_usage) as avg_peak_usage,
        MAX(dp.peak_interval_usage) as absolute_peak_usage,
        AVG(dp.high_usage_intervals) as avg_high_usage_intervals,
        AVG(dp.night_usage) as avg_night_usage,
        AVG(dp.day_usage) as avg_day_usage,
        SUM(dp.fault_intervals) as total_fault_intervals,
        AVG(dp.fault_intervals) as avg_daily_faults,
        AVG(dp.min_interval_usage) / AVG(dp.daily_usage) as baseline_ratio,
        AVG(dp.peak_interval_usage) / AVG(dp.daily_usage) as peak_ratio,
        STDDEV(dp.daily_usage) / AVG(dp.daily_usage) as variability_coefficient,
        AVG(CASE WHEN dp.day_of_week IN (1, 7) THEN dp.daily_usage END) as weekend_usage,
        AVG(CASE WHEN dp.day_of_week NOT IN (1, 7) THEN dp.daily_usage END) as weekday_usage
      FROM daily_patterns dp
      INNER JOIN analysis_period ap ON dp.customer_id = ap.customer_id
      GROUP BY dp.customer_id, ap.analysis_days_used, ap.total_days_available, ap.analysis_start_date, ap.last_date
    ),
    comprehensive_analysis AS (
      SELECT 
        em.*,
        ta.early_avg_usage,
        ta.late_avg_usage,
        ta.early_baseline,
        ta.late_baseline,
        ta.winter_usage,
        ta.summer_usage,
        ta.mild_season_usage,
        CASE WHEN ta.late_avg_usage > ta.early_avg_usage * 1.15 THEN TRUE ELSE FALSE END as usage_increased,
        CASE WHEN ta.late_baseline > ta.early_baseline * 1.20 THEN TRUE ELSE FALSE END as baseline_degraded,
        (ta.late_avg_usage - ta.early_avg_usage) / ta.early_avg_usage * 100 as usage_change_percent,
        (ta.late_baseline - ta.early_baseline) / NULLIF(ta.early_baseline, 0) * 100 as baseline_change_percent,
        CASE 
          WHEN ta.summer_usage > ta.mild_season_usage * 1.5 THEN 'Poor Summer Efficiency'
          WHEN ta.winter_usage > ta.mild_season_usage * 1.4 THEN 'Poor Winter Efficiency'
          WHEN ta.summer_usage > ta.mild_season_usage * 1.2 OR ta.winter_usage > ta.mild_season_usage * 1.2 THEN 'Moderate Seasonal Impact'
          ELSE 'Good Seasonal Efficiency'
        END as seasonal_efficiency
      FROM efficiency_metrics em
      LEFT JOIN time_based_analysis ta ON em.customer_id = ta.customer_id
    )
    SELECT 
      *,
      CASE 
        WHEN baseline_ratio > 0.6 THEN 15
        WHEN baseline_ratio > 0.4 THEN 30
        WHEN baseline_ratio > 0.25 THEN 60
        ELSE 85
      END as baseline_score,
      CASE 
        WHEN variability_coefficient > 0.8 THEN 10
        WHEN variability_coefficient > 0.5 THEN 30
        WHEN variability_coefficient > 0.3 THEN 60
        ELSE 90
      END as consistency_score,
      CASE 
        WHEN peak_ratio > 8 THEN 5
        WHEN peak_ratio > 5 THEN 25
        WHEN peak_ratio > 3 THEN 55
        ELSE 85
      END as peak_efficiency_score,
      CASE 
        WHEN usage_increased AND baseline_degraded THEN 10
        WHEN usage_increased OR baseline_degraded THEN 40
        WHEN ABS(usage_change_percent) < 5 THEN 90
        ELSE 70
      END as stability_score,
      CASE 
        WHEN avg_daily_faults > 0.1 THEN 20
        WHEN avg_daily_faults > 0.05 THEN 60
        ELSE 95
      END as equipment_reliability_score
    FROM comprehensive_analysis
    """
        
        
        # Execute the query
        result = execute_query_json_tool(efficiency_analysis_sql)
        result_data = json.loads(result)
        
        if not result_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": "Failed to analyze energy efficiency",
                "details": result_data.get("error", "Unknown error"),
                "customer_id": customer_id
            }, indent=2)
        
        if not result_data.get("data") or len(result_data["data"]) == 0:
            return json.dumps({
                "success": False,
                "error": "No data found for customer",
                "customer_id": customer_id
            }, indent=2)
        
        analysis = result_data["data"][0]
        
        # Calculate comprehensive efficiency score
        baseline_score = analysis["baseline_score"]
        consistency_score = analysis["consistency_score"] 
        peak_score = analysis["peak_efficiency_score"]
        stability_score = analysis["stability_score"]
        equipment_score = analysis["equipment_reliability_score"]
        
        # Weighted overall score
        overall_efficiency_score = (
            baseline_score * 0.25 +      # 25% - Baseline efficiency
            consistency_score * 0.20 +   # 20% - Usage consistency
            peak_score * 0.20 +          # 20% - Peak management
            stability_score * 0.20 +     # 20% - Equipment stability
            equipment_score * 0.15       # 15% - Equipment reliability
        )
        
        # Generate intelligent, personalized recommendations
        recommendations = []
        insights = []
        
        # Baseline usage analysis
        baseline_ratio = analysis["baseline_ratio"]
        if baseline_ratio > 0.5:
            recommendations.append({
                "category": "Critical - Phantom Load Reduction",
                "priority": "High",
                "issue": f"Baseline usage represents {baseline_ratio*100:.1f}% of total consumption",
                "recommendation": "Conduct phantom load audit. Unplug devices when not in use, replace old appliances with ENERGY STAR models, install smart power strips.",
                "potential_savings": f"${(analysis['avg_daily_usage'] * baseline_ratio * 0.3 * 365 * 0.12):.0f}/year",
                "specific_action": f"Your baseline of {analysis['avg_baseline_usage']:.2f} kWh/interval suggests significant always-on loads"
            })
            insights.append(f"⚠️ High phantom loads detected - {baseline_ratio*100:.1f}% of usage is baseline consumption")
        elif baseline_ratio > 0.3:
            recommendations.append({
                "category": "Standby Power Optimization",
                "priority": "Medium",
                "issue": f"Moderate baseline usage at {baseline_ratio*100:.1f}% of consumption",
                "recommendation": "Review standby appliances, consider smart power management.",
                "potential_savings": f"${(analysis['avg_daily_usage'] * baseline_ratio * 0.15 * 365 * 0.12):.0f}/year",
                "specific_action": f"Target reduction of baseline from {analysis['avg_baseline_usage']:.2f} to {analysis['avg_baseline_usage']*0.8:.2f} kWh/interval"
            })
        
        # Equipment degradation analysis
        if analysis["usage_increased"] and analysis["baseline_degraded"]:
            usage_change = analysis["usage_change_percent"]
            baseline_change = analysis["baseline_change_percent"]
            recommendations.append({
                "category": "Equipment Degradation Alert",
                "priority": "High",
                "issue": f"Energy usage increased {usage_change:.1f}% and baseline increased {baseline_change:.1f}% over time",
                "recommendation": "Schedule professional energy audit. Check HVAC system efficiency, inspect appliances for degradation.",
                "potential_savings": f"${(analysis['late_avg_usage'] - analysis['early_avg_usage']) * 365 * 0.12:.0f}/year",
                "specific_action": f"Usage grew from {analysis['early_avg_usage']:.1f} to {analysis['late_avg_usage']:.1f} kWh/day"
            })
            insights.append(f"📈 Equipment degradation detected - usage increased {usage_change:.1f}% over analysis period")
        
        # Peak usage analysis
        peak_ratio = analysis["peak_ratio"]
        if peak_ratio > 6:
            recommendations.append({
                "category": "Extreme Peak Load Management",
                "priority": "High", 
                "issue": f"Peak usage is {peak_ratio:.1f}x your daily average",
                "recommendation": "Investigate cause of extreme peaks. Check for faulty equipment, oversized appliances, or simultaneous high-load usage.",
                "potential_savings": "20-30% through load balancing",
                "specific_action": f"Peak of {analysis['absolute_peak_usage']:.1f} kWh/interval suggests equipment malfunction or inefficiency"
            })
            insights.append(f"🔥 Extreme usage spikes detected - peak is {peak_ratio:.1f}x daily average")
        elif peak_ratio > 4:
            recommendations.append({
                "category": "Peak Load Optimization",
                "priority": "Medium",
                "issue": f"High peak usage at {peak_ratio:.1f}x daily average",
                "recommendation": "Stagger high-energy appliance usage, consider load scheduling.",
                "potential_savings": "10-15% through better timing",
                "specific_action": f"Reduce peak from {analysis['absolute_peak_usage']:.1f} kWh through load shifting"
            })
        
        # Seasonal efficiency analysis
        seasonal_efficiency = analysis["seasonal_efficiency"]
        if "Poor Summer Efficiency" in seasonal_efficiency:
            summer_increase = (analysis["summer_usage"] / analysis["mild_season_usage"] - 1) * 100
            recommendations.append({
                "category": "HVAC Summer Efficiency",
                "priority": "Medium",
                "issue": f"Summer usage {summer_increase:.0f}% higher than mild seasons",
                "recommendation": "Service AC system, improve insulation, use programmable thermostat, seal air leaks.",
                "potential_savings": f"${(analysis['summer_usage'] - analysis['mild_season_usage']) * 90 * 0.12 * 0.2:.0f}/summer",
                "specific_action": f"Summer average: {analysis['summer_usage']:.1f} vs mild season: {analysis['mild_season_usage']:.1f} kWh/day"
            })
            insights.append(f"🌡️ Poor summer efficiency - AC system may need attention")
        elif "Poor Winter Efficiency" in seasonal_efficiency:
            winter_increase = (analysis["winter_usage"] / analysis["mild_season_usage"] - 1) * 100
            recommendations.append({
                "category": "Heating System Efficiency",
                "priority": "Medium",
                "issue": f"Winter usage {winter_increase:.0f}% higher than mild seasons",
                "recommendation": "Service heating system, improve insulation, weatherstrip doors/windows.",
                "potential_savings": f"${(analysis['winter_usage'] - analysis['mild_season_usage']) * 90 * 0.12 * 0.2:.0f}/winter",
                "specific_action": f"Winter average: {analysis['winter_usage']:.1f} vs mild season: {analysis['mild_season_usage']:.1f} kWh/day"
            })
            insights.append(f"❄️ Poor winter efficiency - heating system optimization needed")
        
        # Equipment reliability analysis
        if analysis["avg_daily_faults"] > 0.1:
            recommendations.append({
                "category": "Equipment Reliability Issues",
                "priority": "High",
                "issue": f"Frequent equipment faults detected ({analysis['total_fault_intervals']} total)",
                "recommendation": "Schedule professional inspection of smart meter and electrical system.",
                "potential_savings": "Prevent equipment damage and efficiency loss",
                "specific_action": "Address recurring meter errors, connection issues, and sensor faults"
            })
            insights.append(f"⚡ Equipment reliability concerns - frequent fault reports")
        
        # Consistency analysis  
        variability = analysis["variability_coefficient"]
        if variability > 0.6:
            recommendations.append({
                "category": "Usage Pattern Optimization",
                "priority": "Medium",
                "issue": f"Highly variable daily usage (coefficient: {variability:.2f})",
                "recommendation": "Develop consistent energy habits, use timers and automation for appliances.",
                "potential_savings": "5-10% through habit optimization",
                "specific_action": f"Daily usage ranges from {analysis['min_daily_usage']:.1f} to {analysis['max_daily_usage']:.1f} kWh"
            })
            insights.append(f"📊 Inconsistent usage patterns - opportunity for habit improvement")
        
        # If no major issues found, provide positive reinforcement
        if overall_efficiency_score > 75:
            recommendations.append({
                "category": "Efficiency Maintenance",
                "priority": "Low",
                "issue": "Good overall efficiency",
                "recommendation": "Continue current practices. Consider minor optimizations like LED upgrades, smart thermostats.",
                "potential_savings": "3-5% through minor improvements",
                "specific_action": "Maintain current efficient usage patterns"
            })
            insights.append(f"✅ Good energy efficiency practices - maintain current approach")
        
        # Grade assignment
        if overall_efficiency_score >= 85:
            grade = "A"
        elif overall_efficiency_score >= 70:
            grade = "B" 
        elif overall_efficiency_score >= 55:
            grade = "C"
        elif overall_efficiency_score >= 40:
            grade = "D"
        else:
            grade = "F"
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "analysis_period_info": {
                "total_data_days_available": analysis["total_days_available"],
                "analysis_days_used": analysis["analysis_days_used"],
                "actual_analysis_days": analysis["actual_analysis_days"],
                "analysis_start_date": analysis["analysis_start_date"],
                "analysis_end_date": analysis["analysis_end_date"]
            },
            "efficiency_assessment": {
                "overall_efficiency_score": round(overall_efficiency_score, 1),
                "grade": grade,
                "component_scores": {
                    "baseline_efficiency": baseline_score,
                    "usage_consistency": consistency_score,
                    "peak_management": peak_score,
                    "equipment_stability": stability_score,
                    "equipment_reliability": equipment_score
                }
            },
            "usage_statistics": {
                "avg_daily_usage_kwh": round(analysis["avg_daily_usage"], 2),
                "baseline_usage_kwh": round(analysis["avg_baseline_usage"], 3),
                "baseline_percentage": round(baseline_ratio * 100, 1),
                "peak_usage_kwh": round(analysis["absolute_peak_usage"], 2),
                "peak_ratio": round(peak_ratio, 1),
                "variability_coefficient": round(variability, 3),
                "seasonal_efficiency": seasonal_efficiency
            },
            "trends_analysis": {
                "usage_change_percent": round(analysis["usage_change_percent"] or 0, 1),
                "baseline_change_percent": round(analysis["baseline_change_percent"] or 0, 1),
                "equipment_degradation_detected": analysis["usage_increased"] and analysis["baseline_degraded"],
                "early_period_avg": round(analysis["early_avg_usage"] or 0, 1),
                "late_period_avg": round(analysis["late_avg_usage"] or 0, 1)
            },
            "equipment_health": {
                "total_fault_intervals": analysis["total_fault_intervals"],
                "daily_fault_rate": round(analysis["avg_daily_faults"], 4),
                "reliability_score": equipment_score
            },
            "key_insights": insights,
            "recommendations": recommendations,
            "summary": f"Customer {customer_id} efficiency score: {overall_efficiency_score:.1f}/100 (Grade {grade}). "
                      f"Analysis based on {analysis['actual_analysis_days']} days reveals "
                      f"{len([r for r in recommendations if r['priority'] == 'High'])} high-priority issues and "
                      f"{len(recommendations)} total improvement opportunities. "
                      f"{'Equipment degradation detected. ' if analysis['usage_increased'] and analysis['baseline_degraded'] else ''}"
                      f"Key focus: {recommendations[0]['category'] if recommendations else 'Maintain current efficiency'}."
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error analyzing energy efficiency: {str(e)}",
            "customer_id": customer_id
        }, indent=2)


def get_customer_energy_insights(customer_id: str, analysis_days: int = 365) -> str:
    """
    ADK Tool: Get comprehensive energy insights combining TOU fit and efficiency analysis
    
    This tool provides a complete energy analysis by combining TOU plan fit assessment
    with energy efficiency analysis using all available data OR the last 365 days
    (whichever is smaller) to give customers actionable insights.
    
    Args:
        customer_id: Customer ID to analyze (e.g., 'CUST000001')
        analysis_days: Maximum days to analyze (default: 365)
        
    Returns:
        JSON string with comprehensive energy insights and recommendations
    """
    try:
        # Get TOU analysis
        tou_result = analyze_tou_plan_fit(customer_id, analysis_days)
        tou_data = json.loads(tou_result)
        
        # Get efficiency analysis
        efficiency_result = analyze_energy_efficiency(customer_id, analysis_days)
        efficiency_data = json.loads(efficiency_result)
        
        if not tou_data.get("success") or not efficiency_data.get("success"):
            return json.dumps({
                "success": False,
                "error": "Failed to complete comprehensive analysis",
                "tou_error": tou_data.get("error") if not tou_data.get("success") else None,
                "efficiency_error": efficiency_data.get("error") if not efficiency_data.get("success") else None,
                "customer_id": customer_id
            }, indent=2)
        
        # Combine insights and create action plan
        action_plan = []
        
        # TOU plan recommendation
        if tou_data["cost_analysis"]["annual_savings"] > 50:
            action_plan.append({
                "action": "Switch to TOU Plan",
                "priority": "High",
                "impact": f"Save ${tou_data['cost_analysis']['annual_savings']:.0f}/year",
                "details": tou_data["tou_plan_assessment"]["optimization_tip"]
            })
        
        # Add efficiency recommendations
        for rec in efficiency_data["recommendations"]:
            if rec["priority"] in ["High", "Medium"]:
                action_plan.append({
                    "action": rec["recommendation"],
                    "priority": rec["priority"],
                    "impact": rec["potential_savings"],
                    "category": rec["category"]
                })
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "analysis_summary": {
                "data_period": f"{tou_data['analysis_period_info']['analysis_start_date']} to {tou_data['analysis_period_info']['analysis_end_date']}",
                "days_analyzed": tou_data["analysis_period_info"]["actual_analysis_days"],
                "tou_plan_savings": tou_data["cost_analysis"]["annual_savings"],
                "tou_fit_rating": tou_data["tou_plan_assessment"]["fit_rating"],
                "efficiency_score": efficiency_data["efficiency_assessment"]["overall_efficiency_score"],
                "efficiency_grade": efficiency_data["efficiency_assessment"]["consistency_grade"]
            },
            "action_plan": action_plan,
            "detailed_analysis": {
                "tou_analysis": tou_data,
                "efficiency_analysis": efficiency_data
            }
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error generating comprehensive insights: {str(e)}",
            "customer_id": customer_id
        }, indent=2)