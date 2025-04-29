"""
Configuration settings for the BizScout-AI project.
"""

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
    'output_format': 'parquet',
    'chunk_size': 1000
}

# Location settings
DEFAULT_LOCATION = {
    'latitude': 34.0522,
    'longitude': -118.2437,
    'radius': 5000  # meters
}

# Output settings
OUTPUT = {
    'processed_data': 'data/processed/',
    'semi_processed_data': 'data/semi_processed/',
    'reports': 'data/processed/reports/',
    'models': 'data/processed/models/'
} 