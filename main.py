import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from loaders.api_loader import YelpDeliveryLoader
from loaders.csv_loader import CSVLoader
from loaders.web_scraper import OpentableScraper
from helper.data_processor import process_restaurant_data
from helper.scoring_engine import analyze_clusters
from cleaning.data_cleaner import DataCleaner
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data_sources() -> Dict[str, pd.DataFrame]:
    """
    Load data from all available sources.
    
    Returns:
        Dict[str, pd.DataFrame]: Dictionary of dataframes from each source
    """
    raw_data = {}
    
    # Load Yelp data
    try:
        yelp_loader = YelpDeliveryLoader()
        yelp_data = yelp_loader.load_data()
        if not yelp_data.empty:
            raw_data['Yelp'] = yelp_data
            logger.info(f"Loaded {len(yelp_data)} records from Yelp")
    except Exception as e:
        logger.error(f"Error loading Yelp data: {str(e)}")

    # Load CSV data
    try:
        csv_loader = CSVLoader()
        csv_data = csv_loader.load_data()
        if not csv_data.empty:
            raw_data['CSV'] = csv_data
            logger.info(f"Loaded {len(csv_data)} records from CSV")
    except Exception as e:
        logger.error(f"Error loading CSV data: {str(e)}")

    # Load OpenTable data
    try:
        opentable_scraper = OpentableScraper()
        opentable_data = opentable_scraper.load_data()
        if not opentable_data.empty:
            raw_data['OpenTable'] = opentable_data
            logger.info(f"Loaded {len(opentable_data)} records from OpenTable")
    except Exception as e:
        logger.error(f"Error loading OpenTable data: {str(e)}")

    return raw_data

def save_processed_data(df: pd.DataFrame, output_format: str = 'csv', output_file_name: str = None) -> None:
    """
    Save processed data to file.
    
    Args:
        df (pd.DataFrame): Data to save
        output_format (str): Format to save data in ('csv' or 'json')
        output_file_name (str): Name of the output file
    """
    try:
        output_dir = Path(settings.DATA_DIR) / 'semi_processed'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"{output_file_name}_{timestamp}.{output_format}"
        
        if output_format == 'csv':
            df.to_csv(output_file, index=False)
        elif output_format == 'json':
            df.to_json(output_file, orient='records', lines=True)
            
        logger.info(f"Saved {len(df)} records to {output_file}")
        
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise

def process_data():
    """
    Process and combine data from all sources.
    """
    try:
        # Load data from all sources
        raw_data = load_data_sources()
        if not raw_data:
            logger.error("No data loaded from any source")
            return
            
        # Save data from each source
        for source_name, df in raw_data.items():
            save_processed_data(
                df,
                output_format='csv',
                output_file_name=f"{source_name.lower()}_data"
            )
            
        # Process and combine the data
        logger.info("Processing and combining restaurant data...")
        try:
            combined_data = process_restaurant_data()
            logger.info(f"Successfully combined {len(combined_data)} restaurant records")
            
        except Exception as e:
            logger.error(f"Error processing restaurant data: {str(e)}")
            raise
            
        logger.info("Data processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}")
        raise

def analyze_data(category: str = None):
    """
    Analyze the processed data for cluster insights.
    
    Args:
        category (str, optional): Restaurant category to analyze. If None, analyzes all restaurants.
    """
    try:
        # Find the most recent combined data file
        processed_dir = Path(settings.DATA_DIR) / 'processed'
        combined_files = list(processed_dir.glob('combined_restaurants_*.csv'))
        
        if not combined_files:
            raise FileNotFoundError("No processed data files found")
            
        # Get the most recent file
        latest_file = max(combined_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Reading processed data from {latest_file}")
        
        # Read the combined data
        combined_data = pd.read_csv(latest_file)
        
        # Create final_output directory
        final_output_dir = Path(settings.DATA_DIR) / 'final_output'
        final_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analyze clusters and save to final_output directory
        analyze_clusters(combined_data, final_output_dir, category)
        
        category_msg = f"for {category} restaurants" if category else "for all restaurants"
        logger.info(f"Data analysis completed successfully {category_msg}")
        
    except Exception as e:
        logger.error(f"Error in data analysis: {str(e)}")
        raise

def main():
    """
    Main execution function.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Restaurant Data Processing and Analysis')
    parser.add_argument('--mode', choices=['process', 'analyze', 'both'], 
                      default='both', help='Operation mode: process data, analyze data, or both')
    parser.add_argument('--category', type=str, default=None,
                      help='Restaurant category to analyze (default: None, analyzes all restaurants)')
    
    args = parser.parse_args()
    
    if args.mode in ['process', 'both']:
        process_data()
        
    if args.mode in ['analyze', 'both']:
        analyze_data(args.category)

if __name__ == "__main__":
    main() 