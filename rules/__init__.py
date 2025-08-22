"""
Rules loader for diabetes report system
"""
import json
import os
from pathlib import Path

def load_rules():
    """Load clinical rules and thresholds from rules.json"""
    rules_path = Path(__file__).parent / "rules.json"
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_traffic_light_status(metric_name: str, value: float, rules: dict) -> str:
    """
    Determine traffic light status for a given metric
    
    Returns: 'green', 'amber', or 'red'
    """
    if metric_name not in rules.get('traffic', {}):
        return 'amber'  # Default for unknown metrics
    
    thresholds = rules['traffic'][metric_name]
    
    if value <= thresholds.get('green_max', float('inf')):
        return 'green'
    elif value <= thresholds.get('amber_max', float('inf')):
        return 'amber'
    else:
        return 'red'

def get_traffic_light_emoji(status: str) -> str:
    """Get emoji for traffic light status"""
    return {
        'green': '🟢',
        'amber': '🔶', 
        'red': '🔴'
    }.get(status, '⚪')
