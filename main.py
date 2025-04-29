import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from loaders.api_loader import YelpDeliveryLoader
from loaders.csv_loader import CSVLoader
from loaders.web_scraper import OpentableScraper
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
    Load data from all configured sources.
    
    Returns:
        Dict[str, pd.DataFrame]: Dictionary of DataFrames from each source
    """
    data = {}
    
    # Load Yelp data
    try:
        logger.info("Loading Yelp data...")
        Yelp_loader = YelpDeliveryLoader()
        data['Yelp'] = Yelp_loader.load_data()
        logger.info(f"Loaded {len(data['Yelp'])} records from Yelp")
    except Exception as e:
        logger.error(f"Error loading Yelp data: {str(e)}")
    
    # Load CSV data
    try:
        logger.info("Loading CSV data...")
        csv_loader = CSVLoader()
        csv_data = csv_loader.load_data()
        data.update(csv_data)
        logger.info(f"Loaded {sum(len(df) for df in csv_data.values())} total records from CSV files")
    except Exception as e:
        logger.error(f"Error loading CSV data: {str(e)}")
    
    # Load Opentable data
    try:
        logger.info("Loading Opentable data...")
        opendata_scraper = OpentableScraper()
        data['Opentable'] = opendata_scraper.load_data()
        logger.info(f"Loaded {len(data['Opentable'])} records from Opentable")
    except Exception as e:
        logger.error(f"Error loading Opentable data: {str(e)}")
    
    return data

def clean_and_process_data(raw_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Clean and process data from all sources.
    
    Args:
        raw_data (Dict[str, pd.DataFrame]): Dictionary of raw DataFrames
        
    Returns:
        pd.DataFrame: Cleaned and merged DataFrame
    """
    logger.info("Cleaning and processing data...")
    cleaner = DataCleaner()
    
    try:
        processed_data = cleaner.clean_data(raw_data)
        logger.info(f"Successfully processed {len(processed_data)} records")
        return processed_data
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise

def save_processed_data(data: pd.DataFrame, output_format: str = 'parquet') -> None:
    """
    Save processed data to disk.
    
    Args:
        data (pd.DataFrame): Processed data to save
        output_format (str): Format to save data in ('parquet' or 'csv')
    """
    output_dir = Path(settings.OUTPUT['processed_data'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f"processed_data_{timestamp}"
    
    try:
        if output_format == 'parquet':
            output_path = output_path.with_suffix('.parquet')
            data.to_parquet(output_path, index=False)
        else:
            output_path = output_path.with_suffix('.csv')
            data.to_csv(output_path, index=False)
            
        logger.info(f"Saved processed data to {output_path}")
    except Exception as e:
        logger.error(f"Error saving processed data: {str(e)}")
        raise

def main():
    """
    Main execution function.
    """
    try:
        # Load data from all sources
        raw_data = load_data_sources()
        if not raw_data:
            logger.error("No data loaded from any source")
            return
        print(raw_data)
        # # Clean and process the data
        processed_data = clean_and_process_data(raw_data)
        
        # Save the processed data
        save_processed_data(
            processed_data,
            output_format=settings.PROCESSING['output_format']
        )
        
        logger.info("Data processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 