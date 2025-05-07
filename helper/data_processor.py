import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def process_restaurant_data() -> pd.DataFrame:
    """
    Process and combine restaurant data from Yelp and OpenTable.
    
    Returns:
        pd.DataFrame: Combined and processed restaurant data
    """
    try:
        # Load Yelp data
        yelp_file = list(Path('data/semi_processed').glob('yelp_data_*.csv'))[-1]
        yelp_df = pd.read_csv(yelp_file)
        
        # Load OpenTable data
        opentable_file = list(Path('data/semi_processed').glob('opentable_data_*.csv'))[-1]
        opentable_df = pd.read_csv(opentable_file)
        
        # Process Yelp data
        yelp_processed = _process_yelp_data(yelp_df)
        
        # Process OpenTable data
        opentable_processed = _process_opentable_data(opentable_df)
        
        # Combine datasets
        combined_df = pd.concat([yelp_processed, opentable_processed], ignore_index=True)
        
        # Drop duplicates based on name, lat, and long
        combined_df = combined_df.drop_duplicates(subset=['name', 'lat', 'long'])
        
        # Save processed data
        output_dir = Path('data/processed')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'combined_restaurants_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv'
        combined_df.to_csv(output_file, index=False)
        logger.info(f"Saved combined data to {output_file}")
        
        return combined_df
        
    except Exception as e:
        logger.error(f"Error processing restaurant data: {str(e)}")
        raise

def _process_yelp_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process Yelp data to match required format."""
    processed = df.copy()
    
    # Convert categories to list if it's a string
    if isinstance(processed['categories'].iloc[0], str):
        processed['categories'] = processed['categories'].apply(eval)
    
    # Extract lat and long from coordinates
    processed['lat'] = processed['coordinates'].apply(lambda x: eval(x)['latitude'])
    processed['long'] = processed['coordinates'].apply(lambda x: eval(x)['longitude'])
    
    # Map price to numeric category
    price_map = {'$': 1, '$$': 2, '$$$': 3, '$$$$': 4}
    processed['price_category'] = processed['price'].map(price_map).fillna(2)  # Default to 2 if no price info
    
    # Select and rename columns
    return processed[[
        'id', 'name', 'review_count', 'rating', 
        'categories', 'lat', 'long', 'price_category', 'cluster_id'
    ]].assign(source='yelp')

def _process_opentable_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process OpenTable data to match required format."""
    processed = df.copy()
    
    # Map price band to numeric category
    price_map = {
        'Budget': 1,
        'Moderate': 2,
        'Expensive': 3,
        'Very Expensive': 4
    }
    processed['price_category'] = processed['priceBand'].map(price_map).fillna(2)
    
    # Convert categories to list format
    processed['categories'] = processed['primaryCuisine'].apply(lambda x: [x] if pd.notna(x) else [])
    
    # Select and rename columns
    return processed[[
        'restaurantId', 'name', 'reviewCount', 'rating',
        'categories', 'latitude', 'longitude', 'price_category', 'cluster_id'
    ]].rename(columns={
        'restaurantId': 'id',
        'reviewCount': 'review_count',
        'latitude': 'lat',
        'longitude': 'long'
    }).assign(source='opentable') 