"""
Configuration module for market analysis
Shared between GUI and analysis scripts
"""
import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "companies_per_sector": 10,
    "active_sectors": ["electricity", "oil-gas", "semiconductors", "software", "energy", "defense"],
    "weights": {
        "roic": 0.25,
        "fcf": 0.20,
        "cash_quality": 0.15,
        "leverage": 0.15,
        "growth": 0.10,
        "other": 0.15
    }
}

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_config():
    """Load configuration from file, or return defaults"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def get_weight(metric_name):
    """Get weight for a specific metric"""
    config = load_config()
    return config["weights"].get(metric_name, 0.0)

def get_companies_per_sector():
    """Get number of companies per sector"""
    config = load_config()
    return config.get("companies_per_sector", 10)

def get_active_sectors():
    """Get list of active sectors"""
    config = load_config()
    return config.get("active_sectors", DEFAULT_CONFIG["active_sectors"])
