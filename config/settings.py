"""
Configuration settings for the BizScout-AI project.
"""
from .api_keys import YELP_API_KEY

# Base directory for all data
DATA_DIR = 'data'

# API Keys for various services
API_KEYS = {
    'yelp': YELP_API_KEY
}

# Data source configurations
DATA_SOURCES = {
    'yelp': {
        'base_url': 'https://api.yelp.com/v3/transactions/delivery/search',
        'limit': 50
    },
    'opentable': {
        'base_url': 'https://www.opentable.com',
        'search_path': '/s',
        'max_pages': 1
    },
    'csv': {
        'zoning_file': 'data/raw/la_zoning_1.csv'
    }
}

# Data processing settings
PROCESSING = {
    'clean_threshold': 0.8,  # Minimum data completeness threshold
    'output_format': 'csv',  # Changed to CSV for semi-processed data
    'chunk_size': 1000,
    'delay_between_requests': 5  # Delay in seconds between API requests
}

# Location settings - List of coordinates to process
LOCATIONS = [
    {
        'latitude': 34.0522,
        'longitude': -118.2437,
        'radius': 5000  # meters
    },
    {
        'latitude': 34.0928,
        'longitude': -118.3287,
        'radius': 5000
    },
    {
        'latitude': 34.0195,
        'longitude': -118.4912,
        'radius': 5000
    }
]

# Output settings
OUTPUT = {
    'processed_data': 'data/processed/',
    'semi_processed_data': {
        'yelp': 'data/semi_processed/yelp/',
        'opentable': 'data/semi_processed/opentable/',
        'csv': 'data/semi_processed/csv/'
    },
    'reports': 'data/processed/reports/',
    'models': 'data/processed/models/'
} 