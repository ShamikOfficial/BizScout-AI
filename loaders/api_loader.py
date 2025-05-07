"""
API data loader implementation for Yelp data.
"""
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import json
import time
import requests
from .base_loader import BaseLoader
from config import settings

class YelpDeliveryLoader(BaseLoader):
    """
    Loader for Yelp API data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Yelp API loader.
        
        Args:
            config (Dict[str, Any], optional): Configuration override
        """
        super().__init__(config)
        self.api_key = settings.API_KEYS['yelp']
        self.base_url = "https://api.yelp.com/v3"
        self.centroids_file = Path(settings.DATA_DIR) / 'semi_processed' / 'cluster_centroids.json'
        self.centroids = self._load_centroids()
        
    def _load_centroids(self) -> Dict[str, Dict[str, float]]:
        """
        Load cluster centroids from JSON file.
        
        Returns:
            Dict[str, Dict[str, float]]: Dictionary of cluster centroids
        """
        try:
            if not self.centroids_file.exists():
                raise FileNotFoundError(f"Centroids file not found: {self.centroids_file}")
                
            with open(self.centroids_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logging.error(f"Error loading centroids: {str(e)}")
            raise
    
    def load_data(self) -> pd.DataFrame:
        """
        Load data from Yelp API.
        
        Returns:
            pd.DataFrame: DataFrame containing API data
        """
        try:
            all_data = []
            
            # Process each cluster centroid
            for cluster_id, coords in self.centroids.items():
                logging.info(f"Loading Yelp data for cluster {cluster_id} at coordinates: ({coords['latitude']}, {coords['longitude']})")
                
                # Get data for this location
                location_data = self._get_location_data(coords['latitude'], coords['longitude'])
                all_data.extend(location_data)
                
                # Add cluster information
                for item in location_data:
                    item['cluster_id'] = cluster_id
                
                # Log count of items for this location
                logging.info(f"Found {len(location_data)} businesses at coordinates ({coords['latitude']}, {coords['longitude']})")
                
                # Respect rate limits with 3 second delay
                time.sleep(3)
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            
            # Drop duplicate rows based on business ID
            df = df.drop_duplicates(subset=['id'], keep='first')
            
            logging.info(f"Loaded {len(df)} unique businesses from Yelp API")
            
            return df
            
        except Exception as e:
            logging.error(f"Error loading Yelp data: {str(e)}")
            raise
    
    def _get_location_data(self, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Get data for a specific location from Yelp API.
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            List[Dict[str, Any]]: List of business data
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'radius': 1000,  # 1km radius
                'limit': 50,
                'offset': 51
            }
            
            response = requests.get(
                f"{self.base_url}/businesses/search",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('businesses', [])
            else:
                logging.error(f"API request failed with status {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Error getting location data: {str(e)}")
            return []
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate the API data.
        
        Args:
            data (pd.DataFrame): DataFrame to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if data.empty:
            return False
            
        required_columns = ['id', 'name', 'latitude', 'longitude', 'categories', 'cluster_id']
        return all(col in data.columns for col in required_columns)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the API data.
        
        Returns:
            Dict[str, Any]: Metadata about the API data
        """
        metadata = super().get_metadata()
        metadata.update({
            'centroids_file': str(self.centroids_file.absolute()),
            'n_clusters': len(self.centroids)
        })
        return metadata
