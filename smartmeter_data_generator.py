import json
import random
import csv
from datetime import datetime, timedelta
import math
import os

def generate_smartmeter_data_all_customers():
    """
    Generate smartmeter data for 30 customers with DECOUPLED TOU fit and energy efficiency patterns.
    
    TOU Fit and Energy Efficiency are now separate characteristics:
    - A customer can have excellent TOU fit but poor efficiency (e.g., EV charging at night with old appliances)
    - A customer can have poor TOU fit but good efficiency (e.g., efficient appliances used during day)
    - Equipment degradation, seasonal issues, and device failures are modeled separately
    
    Customer patterns (6 customers each):
    - Group 1: Excellent TOU + High Efficiency
    - Group 2: Excellent TOU + Poor Efficiency  
    - Group 3: Poor TOU + High Efficiency
    - Group 4: Poor TOU + Poor Efficiency
    - Group 5: Mixed scenarios with equipment issues and degradation
    """
    
    # Generate data for 395 days (13 months to show seasonal patterns)
    start_date = datetime(2024, 1, 1)  # Start from beginning of 2024
    
    all_data = []
    
    # Customer pattern definitions - TOU and Efficiency are now SEPARATE
    customer_patterns = {
        # Group 1: Excellent TOU fit + High efficiency (ideal customers)
        'excellent_tou_high_eff': {
            'range': range(1, 11),
            'tou_params': {
                'night_usage_pct': (0.65, 0.80),  # 65-80% night usage
                'night_peak_hours': [22, 23, 0, 1, 2, 3],  # When they use most power at night
                'day_usage_factor': 0.3  # Low day usage
            },
            'efficiency_params': {
                'base_usage': (0.2, 0.4),  # Low baseline (efficient appliances)
                'peak_multiplier': (1.5, 2.0),  # Moderate peaks
                'variability': (0.05, 0.15),  # Very consistent usage
                'equipment_degradation': False,
                'seasonal_hvac_efficiency': 0.9  # Efficient HVAC
            },
            'description': 'EV owners with efficient appliances, night shift workers with good habits'
        },
        
        # Group 2: Excellent TOU fit + Poor efficiency (night users with inefficient equipment)
        'excellent_tou_poor_eff': {
            'range': range(11, 21),
            'tou_params': {
                'night_usage_pct': (0.60, 0.75),  # Good night usage
                'night_peak_hours': [20, 21, 22, 23, 0, 1],
                'day_usage_factor': 0.4
            },
            'efficiency_params': {
                'base_usage': (0.8, 1.2),  # High baseline (phantom loads, old appliances)
                'peak_multiplier': (3.0, 5.0),  # Very high peaks
                'variability': (0.3, 0.5),  # Inconsistent usage
                'equipment_degradation': True,
                'seasonal_hvac_efficiency': 0.6  # Inefficient HVAC
            },
            'description': 'Night workers with old appliances, high phantom loads, EV + old house'
        },
        
        # Group 3: Poor TOU fit + High efficiency (day users with efficient equipment)
        'poor_tou_high_eff': {
            'range': range(21, 31),
            'tou_params': {
                'night_usage_pct': (0.15, 0.30),  # Low night usage
                'night_peak_hours': [6, 7],  # Only morning usage
                'day_usage_factor': 1.2  # Higher day usage
            },
            'efficiency_params': {
                'base_usage': (0.2, 0.5),  # Low baseline
                'peak_multiplier': (1.8, 2.5),  # Moderate peaks
                'variability': (0.1, 0.25),  # Consistent usage
                'equipment_degradation': False,
                'seasonal_hvac_efficiency': 0.85
            },
            'description': 'Efficient homes but work-from-home, modern appliances used during day'
        },
        
        # Group 4: Poor TOU fit + Poor efficiency (worst case)
        'poor_tou_poor_eff': {
            'range': range(31, 41),
            'tou_params': {
                'night_usage_pct': (0.10, 0.25),  # Very low night usage
                'night_peak_hours': [7],  # Minimal night usage
                'day_usage_factor': 1.8  # Heavy day usage
            },
            'efficiency_params': {
                'base_usage': (1.0, 2.0),  # Very high baseline
                'peak_multiplier': (4.0, 7.0),  # Extreme peaks
                'variability': (0.4, 0.7),  # Very inconsistent
                'equipment_degradation': True,
                'seasonal_hvac_efficiency': 0.5  # Very inefficient HVAC
            },
            'description': 'Old homes, inefficient appliances, heavy day usage, poor habits'
        },
        
        # Group 5: Mixed scenarios with equipment issues and degradation
        'mixed_issues': {
            'range': range(41, 51),
            'tou_params': {
                'night_usage_pct': (0.25, 0.55),  # Varies by customer
                'night_peak_hours': [22, 23, 0, 1, 6, 7],
                'day_usage_factor': 0.8
            },
            'efficiency_params': {
                'base_usage': (0.5, 1.5),  # Varies
                'peak_multiplier': (2.0, 6.0),  # Wide range
                'variability': (0.2, 0.6),  # Varies
                'equipment_degradation': True,
                'seasonal_hvac_efficiency': 0.7,
                'special_issues': True  # Has equipment failures, HVAC issues, etc.
            },
            'description': 'Mixed scenarios: equipment failures, seasonal issues, device degradation'
        }
    }
    
    print("Starting data generation for all 30 customers with decoupled TOU/efficiency patterns...")
    
    for pattern_name, pattern_config in customer_patterns.items():
        print(f"Generating {pattern_name} customers...")
        
        for i in pattern_config['range']:
            customer_id = f"CUST{i:06d}"
            account_id = f"ACC{i:08d}"
            meter_id = f"SM{i:06d}"
            
            # Generate TOU-specific parameters
            tou_params = pattern_config['tou_params']
            night_pct = random.uniform(*tou_params['night_usage_pct'])
            night_peak_hours = tou_params['night_peak_hours']
            day_usage_factor = tou_params['day_usage_factor']
            
            # Generate efficiency-specific parameters
            eff_params = pattern_config['efficiency_params']
            base_usage = random.uniform(*eff_params['base_usage'])
            peak_multiplier = random.uniform(*eff_params['peak_multiplier'])
            variability = random.uniform(*eff_params['variability'])
            has_degradation = eff_params['equipment_degradation']
            hvac_efficiency = eff_params['seasonal_hvac_efficiency']
            has_special_issues = eff_params.get('special_issues', False)
            
            customer_data = []
            
            # Equipment degradation timeline (for customers with degradation)
            degradation_start_day = random.randint(100, 200) if has_degradation else None
            hvac_failure_day = random.randint(180, 300) if has_special_issues else None
            device_failure_day = random.randint(50, 150) if has_special_issues else None
            
            # Generate data for 395 days
            for day in range(395):
                current_date = start_date + timedelta(days=day)
                
                # Calculate degradation factor
                degradation_factor = 1.0
                if has_degradation and degradation_start_day and day > degradation_start_day:
                    # Equipment gets less efficient over time
                    days_since_degradation = day - degradation_start_day
                    degradation_factor = 1 + (days_since_degradation / 200) * 0.5  # 50% efficiency loss over ~200 days
                
                # Special issue factors
                hvac_issue_factor = 1.0
                device_issue_factor = 1.0
                
                if has_special_issues:
                    # HVAC failure causing higher usage
                    if hvac_failure_day and day > hvac_failure_day:
                        hvac_issue_factor = 1.8  # HVAC working harder
                    
                    # Device failure causing random spikes
                    if device_failure_day and day > device_failure_day:
                        if random.random() < 0.1:  # 10% chance per day
                            device_issue_factor = random.uniform(2.0, 4.0)
                
                # Generate 24 hours of 15-minute intervals (96 intervals per day)
                for hour in range(24):
                    for interval_15min in range(0, 4):
                        
                        # Determine if this is night time (8PM-8AM)
                        is_night = hour >= 20 or hour < 8
                        
                        # Seasonal factors
                        day_of_year = current_date.timetuple().tm_yday
                        # HVAC load varies by season
                        seasonal_hvac_factor = 1 + 0.4 * math.sin(2 * math.pi * (day_of_year - 81) / 365)  # Peak in summer
                        seasonal_hvac_factor *= hvac_efficiency  # Apply HVAC efficiency
                        
                        daily_random = random.gauss(1, variability)
                        
                        # TOU-based usage calculation
                        if is_night:
                            if hour in night_peak_hours:
                                # Peak night usage for this customer's TOU pattern
                                tou_usage = base_usage * peak_multiplier * (1.5 + random.uniform(0, 0.8))
                            else:
                                # Regular night usage
                                tou_usage = base_usage * (1.0 + random.uniform(0, 0.3))
                        else:
                            # Day usage based on TOU pattern
                            if pattern_name.startswith('poor_tou'):
                                # Heavy day users
                                if hour in [9, 10, 11, 13, 14, 15, 18, 19]:  # Peak day hours
                                    tou_usage = base_usage * peak_multiplier * day_usage_factor * (1.5 + random.uniform(0, 1.0))
                                else:
                                    tou_usage = base_usage * day_usage_factor * (1.0 + random.uniform(0, 0.5))
                            else:
                                # Light day users (good TOU)
                                if hour in [7, 8, 18, 19]:  # Morning/evening only
                                    tou_usage = base_usage * peak_multiplier * day_usage_factor * (0.8 + random.uniform(0, 0.4))
                                else:
                                    tou_usage = base_usage * day_usage_factor * (0.5 + random.uniform(0, 0.3))
                        
                        # Apply efficiency factors
                        usage = tou_usage * seasonal_hvac_factor * daily_random
                        usage *= degradation_factor * hvac_issue_factor * device_issue_factor
                        
                        # Special scenarios for mixed_issues group
                        if has_special_issues:
                            # Random equipment spikes
                            if random.random() < 0.005:  # 0.5% chance
                                usage *= random.uniform(3, 8)  # Major spike
                            
                            # Water heater efficiency issues in winter
                            if day_of_year in range(350, 365) or day_of_year in range(1, 80):
                                if hour in [6, 7, 18, 19, 20]:  # Water heater usage times
                                    usage *= 1.4  # 40% more energy for hot water
                        
                        # Ensure usage is positive and reasonable
                        usage = max(0.1, min(usage, 20.0))  # Cap at 20 kWh for extreme cases
                        
                        # Create timestamp
                        minute = interval_15min * 15
                        timestamp = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # Add equipment faults (more likely for degraded equipment)
                        faulty_equipment = None
                        fault_chance = 0.001
                        if has_degradation and day > (degradation_start_day or 0):
                            fault_chance = 0.003  # Higher chance for degraded equipment
                        
                        if random.random() < fault_chance:
                            faulty_equipment = random.choice([
                                'meter_error', 'connection_issue', 'calibration_drift',
                                'hvac_sensor_fault', 'smart_meter_comm_error'
                            ])
                        
                        record = {
                            "customer_id": customer_id,
                            "account_id": account_id,
                            "meter_id": meter_id,
                            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z",  # ISO format with milliseconds
                            "date": current_date.strftime("%Y-%m-%d"),
                            "hour": str(hour),
                            "interval_15min": str(interval_15min),
                            "usage": f"{usage:.3f}",
                            "faulty_equipment": faulty_equipment if faulty_equipment else ""
                        }
                        
                        customer_data.append(record)
            
            all_data.extend(customer_data)
            print(f"  Generated data for {customer_id} ({pattern_name}) - {len(customer_data)} records")
    
    # Shuffle data to make it more realistic
    random.shuffle(all_data)
    
    return all_data

def generate_single_customer_data(customer_id="CUST000001", pattern_type="excellent_tou_high_eff", days=395):
    """
    Generate smartmeter data for a single customer with decoupled TOU and efficiency patterns
    
    Args:
        customer_id: Customer ID (e.g., 'CUST000001')
        pattern_type: Type of pattern ('excellent_tou_high_eff', 'excellent_tou_poor_eff', 
                     'poor_tou_high_eff', 'poor_tou_poor_eff', 'mixed_issues')
        days: Number of days to generate (default: 395)
    
    Returns:
        List of dictionaries containing smartmeter data
    """
    
    start_date = datetime(2024, 1, 1)
    account_id = f"ACC{customer_id[4:]:0>8}"
    meter_id = f"SM{customer_id[4:]}"
    
    # Pattern configurations with decoupled TOU and efficiency
    patterns = {
        'excellent_tou_high_eff': {
            'tou_params': {
                'night_usage_pct': (0.65, 0.80),
                'night_peak_hours': [22, 23, 0, 1, 2, 3],
                'day_usage_factor': 0.3
            },
            'efficiency_params': {
                'base_usage': (0.2, 0.4),
                'peak_multiplier': (1.5, 2.0),
                'variability': (0.05, 0.15),
                'equipment_degradation': False,
                'seasonal_hvac_efficiency': 0.9
            }
        },
        'excellent_tou_poor_eff': {
            'tou_params': {
                'night_usage_pct': (0.60, 0.75),
                'night_peak_hours': [20, 21, 22, 23, 0, 1],
                'day_usage_factor': 0.4
            },
            'efficiency_params': {
                'base_usage': (0.8, 1.2),
                'peak_multiplier': (3.0, 5.0),
                'variability': (0.3, 0.5),
                'equipment_degradation': True,
                'seasonal_hvac_efficiency': 0.6
            }
        },
        'poor_tou_high_eff': {
            'tou_params': {
                'night_usage_pct': (0.15, 0.30),
                'night_peak_hours': [6, 7],
                'day_usage_factor': 1.2
            },
            'efficiency_params': {
                'base_usage': (0.2, 0.5),
                'peak_multiplier': (1.8, 2.5),
                'variability': (0.1, 0.25),
                'equipment_degradation': False,
                'seasonal_hvac_efficiency': 0.85
            }
        },
        'poor_tou_high_eff': {
            'tou_params': {
                'night_usage_pct': (0.15, 0.30),
                'night_peak_hours': [6, 7],
                'day_usage_factor': 1.2
            },
            'efficiency_params': {
                'base_usage': (0.2, 0.5),
                'peak_multiplier': (1.8, 2.5),
                'variability': (0.1, 0.25),
                'equipment_degradation': False,
                'seasonal_hvac_efficiency': 0.85
            }
        },
        'poor_tou_poor_eff': {
            'tou_params': {
                'night_usage_pct': (0.10, 0.25),
                'night_peak_hours': [7],
                'day_usage_factor': 1.8
            },
            'efficiency_params': {
                'base_usage': (1.0, 2.0),
                'peak_multiplier': (4.0, 7.0),
                'variability': (0.4, 0.7),
                'equipment_degradation': True,
                'seasonal_hvac_efficiency': 0.5
            }
        },
        'mixed_issues': {
            'tou_params': {
                'night_usage_pct': (0.25, 0.55),
                'night_peak_hours': [22, 23, 0, 1, 6, 7],
                'day_usage_factor': 0.8
            },
            'efficiency_params': {
                'base_usage': (0.5, 1.5),
                'peak_multiplier': (2.0, 6.0),
                'variability': (0.2, 0.6),
                'equipment_degradation': True,
                'seasonal_hvac_efficiency': 0.7,
                'special_issues': True
            }
        }
    }
    
    if pattern_type not in patterns:
        pattern_type = 'excellent_tou_high_eff'
        print(f"Unknown pattern type, using 'excellent_tou_high_eff'")
    
    pattern = patterns[pattern_type]
    
    # Generate TOU parameters
    tou_params = pattern['tou_params']
    night_pct = random.uniform(*tou_params['night_usage_pct'])
    night_peak_hours = tou_params['night_peak_hours']
    day_usage_factor = tou_params['day_usage_factor']
    
    # Generate efficiency parameters
    eff_params = pattern['efficiency_params']
    base_usage = random.uniform(*eff_params['base_usage'])
    peak_multiplier = random.uniform(*eff_params['peak_multiplier'])
    variability = random.uniform(*eff_params['variability'])
    has_degradation = eff_params['equipment_degradation']
    hvac_efficiency = eff_params['seasonal_hvac_efficiency']
    has_special_issues = eff_params.get('special_issues', False)
    
    customer_data = []
    
    # Equipment issue timelines
    degradation_start_day = random.randint(100, 200) if has_degradation else None
    hvac_failure_day = random.randint(180, 300) if has_special_issues else None
    device_failure_day = random.randint(50, 150) if has_special_issues else None
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Apply same logic as in main function
        degradation_factor = 1.0
        if has_degradation and degradation_start_day and day > degradation_start_day:
            days_since_degradation = day - degradation_start_day
            degradation_factor = 1 + (days_since_degradation / 200) * 0.5
        
        hvac_issue_factor = 1.0
        device_issue_factor = 1.0
        
        if has_special_issues:
            if hvac_failure_day and day > hvac_failure_day:
                hvac_issue_factor = 1.8
            
            if device_failure_day and day > device_failure_day:
                if random.random() < 0.1:
                    device_issue_factor = random.uniform(2.0, 4.0)
        
        for hour in range(24):
            for interval_15min in range(4):
                
                is_night = hour >= 20 or hour < 8
                
                day_of_year = current_date.timetuple().tm_yday
                seasonal_hvac_factor = 1 + 0.4 * math.sin(2 * math.pi * (day_of_year - 81) / 365)
                seasonal_hvac_factor *= hvac_efficiency
                
                daily_random = random.gauss(1, variability)
                
                if is_night:
                    if hour in night_peak_hours:
                        tou_usage = base_usage * peak_multiplier * (1.5 + random.uniform(0, 0.8))
                    else:
                        tou_usage = base_usage * (1.0 + random.uniform(0, 0.3))
                else:
                    if pattern_type.startswith('poor_tou'):
                        if hour in [9, 10, 11, 13, 14, 15, 18, 19]:
                            tou_usage = base_usage * peak_multiplier * day_usage_factor * (1.5 + random.uniform(0, 1.0))
                        else:
                            tou_usage = base_usage * day_usage_factor * (1.0 + random.uniform(0, 0.5))
                    else:
                        if hour in [7, 8, 18, 19]:
                            tou_usage = base_usage * peak_multiplier * day_usage_factor * (0.8 + random.uniform(0, 0.4))
                        else:
                            tou_usage = base_usage * day_usage_factor * (0.5 + random.uniform(0, 0.3))
                
                usage = tou_usage * seasonal_hvac_factor * daily_random
                usage *= degradation_factor * hvac_issue_factor * device_issue_factor
                
                if has_special_issues:
                    if random.random() < 0.005:
                        usage *= random.uniform(3, 8)
                    
                    if day_of_year in range(350, 365) or day_of_year in range(1, 80):
                        if hour in [6, 7, 18, 19, 20]:
                            usage *= 1.4
                
                usage = max(0.1, min(usage, 20.0))
                
                minute = interval_15min * 15
                timestamp = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                faulty_equipment = None
                fault_chance = 0.001
                if has_degradation and day > (degradation_start_day or 0):
                    fault_chance = 0.003
                
                if random.random() < fault_chance:
                    faulty_equipment = random.choice([
                        'meter_error', 'connection_issue', 'calibration_drift',
                        'hvac_sensor_fault', 'smart_meter_comm_error'
                    ])
                
                record = {
                    "customer_id": customer_id,
                    "account_id": account_id,
                    "meter_id": meter_id,
                    "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z",  # ISO format with milliseconds
                    "date": current_date.strftime("%Y-%m-%d"),
                    "hour": str(hour),
                    "interval_15min": str(interval_15min),
                    "usage": f"{usage:.3f}",
                    "faulty_equipment": faulty_equipment if faulty_equipment else ""
                }
                
                customer_data.append(record)
    
    return customer_data

def save_all_customers_to_txt(filename="smartmeter_data_30_customers.txt", delimiter=","):
    """Save generated data for all 30 customers to text file as CSV format"""
    print("Generating data for all 30 customers with decoupled TOU/efficiency patterns...")
    data = generate_smartmeter_data_all_customers()
    
    # Define column headers
    headers = ['customer_id', 'account_id', 'meter_id', 'timestamp', 'date', 'hour', 'interval_15min', 'usage', 'faulty_equipment']
    
    with open(filename, 'w') as f:
        # Write header row
        f.write(delimiter.join(headers) + '\n')
        
        # Write data rows
        for record in data:
            row_values = []
            for header in headers:
                value = record.get(header, '')
                # Handle None values
                if value is None:
                    value = ''
                row_values.append(str(value))
            f.write(delimiter.join(row_values) + '\n')
    
    print(f"Data saved to {filename}")
    print(f"Format: Comma-delimited CSV format")
    print(f"Total records: {len(data):,}")
    print(f"Columns: {', '.join(headers)}")
    print(f"File size: {os.path.getsize(filename) / (1024*1024):.1f} MB")
    return data

def save_random_customer_to_csv(filename="random_customer_data.csv", days=395):
    """Generate and save CSV data for a random customer"""
    
    # Select random customer and pattern
    customer_num = random.randint(1, 30)
    customer_id = f"CUST{customer_num:06d}"
    
    patterns = ['excellent_tou_high_eff', 'excellent_tou_poor_eff', 'poor_tou_high_eff', 'poor_tou_poor_eff', 'mixed_issues']
    pattern_type = random.choice(patterns)
    
    print(f"Generating CSV for {customer_id} with {pattern_type} pattern...")
    
    data = generate_single_customer_data(customer_id, pattern_type, days)
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['customer_id', 'account_id', 'meter_id', 'timestamp', 'date', 'hour', 'interval_15min', 'usage', 'faulty_equipment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for record in data:
            writer.writerow(record)
    
    print(f"CSV saved to {filename}")
    print(f"Customer: {customer_id}")
    print(f"Pattern: {pattern_type}")
    print(f"Records: {len(data):,}")
    print(f"Date range: {data[0]['date']} to {data[-1]['date']}")
    
    return data

def save_random_customer_to_txt(filename="random_customer_data.txt", days=395, delimiter=","):
    """Generate and save CSV format text file for a random customer"""
    
    # Select random customer and pattern
    customer_num = random.randint(1, 30)
    customer_id = f"CUST{customer_num:06d}"
    
    patterns = ['excellent_tou_high_eff', 'excellent_tou_poor_eff', 'poor_tou_high_eff', 'poor_tou_poor_eff', 'mixed_issues']
    pattern_type = random.choice(patterns)
    
    print(f"Generating CSV format text file for {customer_id} with {pattern_type} pattern...")
    
    data = generate_single_customer_data(customer_id, pattern_type, days)
    
    # Define column headers
    headers = ['customer_id', 'account_id', 'meter_id', 'timestamp', 'date', 'hour', 'interval_15min', 'usage', 'faulty_equipment']
    
    # Write to text file as CSV format
    with open(filename, 'w') as f:
        # Write header row
        f.write(delimiter.join(headers) + '\n')
        
        # Write data rows
        for record in data:
            row_values = []
            for header in headers:
                value = record.get(header, '')
                # Handle None values
                if value is None:
                    value = ''
                row_values.append(str(value))
            f.write(delimiter.join(row_values) + '\n')
    
    print(f"CSV format text file saved to {filename}")
    print(f"Format: Comma-delimited CSV format")
    print(f"Customer: {customer_id}")
    print(f"Pattern: {pattern_type}")
    print(f"Records: {len(data):,}")
    print(f"Date range: {data[0]['date']} to {data[-1]['date']}")
    print(f"Columns: {', '.join(headers)}")
    
    return data

def generate_customer_summary():
    """Generate summary of expected customer patterns with decoupled TOU and efficiency"""
    summary = {
        "data_overview": {
            "time_period": "2024-01-01 to 2024-12-30 (395 days, 13+ months)",
            "interval": "15 minutes",
            "total_customers": 30,
            "records_per_customer": 38016,  # 395 days * 24 hours * 4 intervals
            "total_records": 1140480,
            "file_format": "Comma-delimited CSV format"
        },
        "key_improvements": {
            "decoupled_characteristics": "TOU fit and energy efficiency are now separate - customers can have good TOU but poor efficiency or vice versa",
            "equipment_degradation": "Realistic equipment degradation over time causing efficiency loss",
            "seasonal_issues": "HVAC efficiency varies by season, water heater issues in winter",
            "equipment_failures": "Random equipment failures causing usage spikes",
            "longer_timeframe": "395 days to show full seasonal patterns and equipment degradation",
            "optimized_size": "Reduced to 30 customers to keep file size manageable"
        },
        "dataframe_info": {
            "delimiter": "Comma (,)",
            "columns": ["customer_id", "account_id", "meter_id", "timestamp", "date", "hour", "interval_15min", "usage", "faulty_equipment"],
            "timestamp_format": "ISO 8601 format (YYYY-MM-DDTHH:MM:SS.sssZ)",
            "loading_instruction": "pd.read_csv('filename.txt')",
            "sample_row": "CUST000001,ACC00000001,SM000001,2024-01-01T00:00:00.000Z,2024-01-01,0,0,1.234,"
        },
        "customer_patterns": {
            "CUST000001-006": {
                "pattern": "Excellent TOU + High Efficiency",
                "tou_fit": "65-80% night usage",
                "efficiency": "Very High (low baseline, consistent usage)",
                "expected_tou_savings": "$300-600/year",
                "expected_efficiency_score": "85-95",
                "description": "EV owners with efficient appliances, night shift workers with good habits"
            },
            "CUST000007-012": {
                "pattern": "Excellent TOU + Poor Efficiency", 
                "tou_fit": "60-75% night usage",
                "efficiency": "Poor (high baseline, equipment degradation)",
                "expected_tou_savings": "$200-400/year",
                "expected_efficiency_score": "30-50",
                "description": "Night workers with old appliances, high phantom loads, degrading equipment"
            },
            "CUST000013-018": {
                "pattern": "Poor TOU + High Efficiency",
                "tou_fit": "15-30% night usage", 
                "efficiency": "High (efficient equipment, consistent patterns)",
                "expected_tou_savings": "TOU not recommended",
                "expected_efficiency_score": "75-90",
                "description": "Work-from-home with efficient modern appliances used during day"
            },
            "CUST000019-024": {
                "pattern": "Poor TOU + Poor Efficiency",
                "tou_fit": "10-25% night usage",
                "efficiency": "Very Poor (high baseline, extreme peaks, degradation)",
                "expected_tou_savings": "TOU would cost more",
                "expected_efficiency_score": "15-35",
                "description": "Old homes, inefficient appliances, heavy day usage, poor habits"
            },
            "CUST000025-030": {
                "pattern": "Mixed Issues + Equipment Problems",
                "tou_fit": "25-55% night usage (varies)",
                "efficiency": "Poor with specific issues",
                "expected_tou_savings": "Varies by customer",
                "expected_efficiency_score": "20-60",
                "description": "Equipment failures, HVAC issues, seasonal problems, device degradation over time"
            }
        },
        "realistic_scenarios": {
            "equipment_degradation": "Appliances become less efficient over 6-12 months",
            "hvac_seasonal_issues": "Air conditioning efficiency drops in summer, heating issues in winter", 
            "device_failures": "Random spikes from failing appliances (water heater, HVAC, etc.)",
            "phantom_load_growth": "Standby power consumption increases over time",
            "water_heater_winter": "40% higher energy for hot water in winter months"
        }
    }
    
    with open("customer_pattern_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("Enhanced customer pattern summary saved to customer_pattern_summary.json")
    return summary

# Main execution functions
if __name__ == "__main__":
    print("Enhanced Smart Meter Data Simulator")
    print("Decoupled TOU Fit and Energy Efficiency Patterns")
    print("30 Customers | CSV Format | 395 Days")
    print("=" * 60)
    
    # Generate summary first
    print("\n1. Generating enhanced customer pattern summary...")
    summary = generate_customer_summary()
    
    # Option 1: Generate all 30 customers data
    print("\n2. Generate all 30 customers data? (Approx 60-80MB file)")
    print("   395 days of data with decoupled TOU/efficiency patterns")
    print("   Format: Comma-delimited CSV format")
    response = input("Generate all customers? (y/n): ").lower()
    if response == 'y':
        all_data = save_all_customers_to_txt()
        print(f"\nSample of data format:")
        print("customer_id,account_id,meter_id,timestamp,date,hour,interval_15min,usage,faulty_equipment")
        # Show first record as example
        sample = all_data[0]
        headers = ['customer_id', 'account_id', 'meter_id', 'timestamp', 'date', 'hour', 'interval_15min', 'usage', 'faulty_equipment']
        row_values = []
        for header in headers:
            value = sample.get(header, '')
            if value is None:
                value = ''
            row_values.append(str(value))
        print(','.join(row_values))
    
    # Option 2: Generate random customer data
    print("\n3. Generate random customer sample data:")
    print("   a) CSV format")
    print("   b) CSV format as text file")
    
    format_choice = input("Choose format (a/b): ").lower()
    
    if format_choice == 'a':
        csv_data = save_random_customer_to_csv()
    else:
        txt_data = save_random_customer_to_txt()
    
    print("\nFiles generated:")
    print("- customer_pattern_summary.json (enhanced pattern reference)")
    if 'all_data' in locals():
        print("- smartmeter_data_30_customers.txt (all customers - CSV format)")
    if 'csv_data' in locals():
        print("- random_customer_data.csv (single customer sample - CSV)")
    if 'txt_data' in locals():
        print("- random_customer_data.txt (single customer sample - CSV format)")
    
    print("\nEnhanced Features:")
    print("- Decoupled TOU fit and energy efficiency")
    print("- Equipment degradation over time")
    print("- Seasonal HVAC efficiency issues")
    print("- Random equipment failures and spikes")
    print("- 395 days of data (13+ months)")
    print("- ISO 8601 timestamp format")
    print("- Optimized for file size (30 customers)")
    
    print("\nCSV format details:")
    print("- Comma-delimited columns")
    print("- Headers: customer_id,account_id,meter_id,timestamp,date,hour,interval_15min,usage,faulty_equipment")
    print("- Timestamp format: YYYY-MM-DDTHH:MM:SS.sssZ")
    print("- Can be loaded into pandas with: pd.read_csv('filename.txt')")
    print("\nYou can now use this data with the ADK energy analysis tools!")
    print("Expect to see interesting combinations like:")
    print("- Good TOU customers with poor efficiency scores")
    print("- Poor TOU customers with excellent efficiency scores")
    print("- Equipment degradation causing efficiency drops over time")