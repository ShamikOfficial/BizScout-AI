# BizScout-AI: Geo-Intelligent Business Location Recommendation System

A modular and extensible system for analyzing and recommending optimal business locations using multiple data sources.

## Project Structure

```
├── data/                  # Raw and processed data storage
│   ├── raw/              # Original data from sources
│   └── processed/        # Cleaned and transformed data
├── loaders/              # Data loading modules
│   ├── api_loader.py     # Foursquare API integration
│   ├── csv_loader.py     # CSV data loading
│   └── web_scraper.py    # Web scraping functionality
├── cleaning/             # Data cleaning and transformation
│   ├── data_cleaner.py   # Data cleaning utilities
│   └── transformers.py   # Data transformation functions
├── config/               # Configuration files
│   ├── settings.py       # Main configuration
│   └── api_keys.py       # API credentials (gitignored)
├── utils/                # Utility functions
│   └── helpers.py        # Helper functions
├── main.py               # Main driver script
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
```

## Setup and Installation

### 1. Create and Activate Virtual Environment

#### Windows:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate
```

#### Linux/Mac:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `config/api_keys.py` file with your API credentials:
```python
FOURSQUARE_API_KEY = "your_api_key"
YELP_API_KEY = "your_api_key"
```

## Maintainability and Extensibility

### Modular Design
- Each data source has its own loader module
- Data cleaning is separated from data loading
- Configuration is centralized and easily modifiable

### Adapting to Changes
1. **Data Source Changes**:
   - Modify the corresponding loader module
   - Update configuration in `config/settings.py`
   - No changes needed in other modules

2. **New Data Sources**:
   - Create a new loader module in `loaders/`
   - Add configuration in `config/settings.py`
   - Integrate with existing cleaning pipeline

## Usage

1. Ensure your virtual environment is activated
2. Run the main script:
```bash
python main.py
```

## Example Data Processing

```python
from loaders.api_loader import FoursquareLoader
from loaders.csv_loader import CSVLoader
from cleaning.data_cleaner import DataCleaner

# Load data from Foursquare
foursquare_data = FoursquareLoader().load_data()

# Load CSV data
csv_data = CSVLoader().load_data()

# Clean and transform data
cleaner = DataCleaner()
processed_data = cleaner.clean_data(foursquare_data, csv_data)
```

## Dependencies

- Python 3.8+
- pandas
- requests
- beautifulsoup4
- selenium
- python-dotenv
- numpy

## Virtual Environment Management

### Deactivating the Virtual Environment
When you're done working on the project, you can deactivate the virtual environment:
```bash
deactivate
```

### Updating Dependencies
To update the requirements file with new dependencies:
```bash
pip freeze > requirements.txt
```
