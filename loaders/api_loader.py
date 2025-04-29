"""
API data loader implementation for Yelp API.
"""
import requests
import pandas as pd
from typing import Dict, Any, List
import logging
from .base_loader import BaseLoader
from config import settings, api_keys

class YelpDeliveryLoader(BaseLoader):
    """
    Loader for Yelp API delivery transaction search data.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Yelp loader with configuration.
        
        Args:
            config (Dict[str, Any], optional): Override default configuration
        """
        super().__init__(config)
        self.api_key = api_keys.YELP_API_KEY
        self.base_url = settings.DATA_SOURCES['yelp']['base_url']
        self.location = settings.DEFAULT_LOCATION

    def load_data(self) -> pd.DataFrame:
        """
        Load delivery businesses from Yelp API.

        Returns:
            pd.DataFrame: Flattened DataFrame with business info
        """
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }

        params = {
            "latitude": self.location['latitude'],
            "longitude": self.location['longitude']
        }

        response = requests.get(self.base_url, headers=headers, params=params)
        response.raise_for_status()
        businesses = response.json().get("businesses", [])

        return self._parse_businesses(businesses)

    def _parse_businesses(self, businesses: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Flatten Yelp business JSON into DataFrame.

        Args:
            businesses (List[Dict[str, Any]]): Raw business data from Yelp API

        Returns:
            pd.DataFrame: Flattened business information
        """
        parsed = []
        for b in businesses:
            categories = [c['title'] for c in b.get('categories', [])]
            transactions = b.get('transactions', [])
            parsed.append({
                'id': b['id'],
                'name': b['name'],
                'review_count': b.get('review_count'),
                'rating': b.get('rating'),
                'price': b.get('price', None),
                'latitude': b['coordinates']['latitude'],
                'longitude': b['coordinates']['longitude'],
                'categories': categories,
                'features': [t.lower() for t in transactions],  # Delivery, Pickup, etc.
                'is_closed': b.get('is_closed', None),
                'display_address': ", ".join(b['location'].get('display_address', []))
            })
        df=pd.DataFrame(parsed)
        df=df.astype('str')

        return df

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate the loaded Yelp business data.

        Args:
            data (pd.DataFrame): DataFrame to validate

        Returns:
            bool: True if data is valid, False otherwise
        """
        required_columns = ['id', 'name', 'latitude', 'longitude', 'categories']
        return all(col in data.columns for col in required_columns)
