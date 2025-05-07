"""
Web scraper implementation for Opentable data.
"""
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from bs4 import BeautifulSoup
import requests
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_loader import BaseLoader
from config import settings
from datetime import datetime, timedelta
import json

class OpentableScraper(BaseLoader):
    """
    Web scraper for Opentable business data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Opentable scraper with configuration.
        
        Args:
            config (Dict[str, Any], optional): Override default configuration
        """
        super().__init__(config)
        self.base_url = "https://www.opentable.com"
        self.centroids_file = Path(settings.DATA_DIR) / 'semi_processed' / 'cluster_centroids.json'
        self.centroids = self._load_centroids()
        self.max_pages = settings.DATA_SOURCES['opentable']['max_pages']
        self.locations = settings.LOCATIONS
        self.delay = settings.PROCESSING['delay_between_requests']
        
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
        Load data from Opentable website.
        
        Returns:
            pd.DataFrame: DataFrame containing scraped data
        """
        try:
            all_data = []
            
            # Process each cluster centroid
            for cluster_id, coords in self.centroids.items():
                logging.info(f"Loading Opentable data for cluster {cluster_id} at coordinates: ({coords['latitude']}, {coords['longitude']})")
                
                # Scrape data for this location
                location_data = self._scrape_location(coords['latitude'], coords['longitude'])
                all_data.extend(location_data)
                
                # Add cluster information
                for item in location_data:
                    item['cluster_id'] = cluster_id
                
                # Log count of items for this location
                logging.info(f"Found {len(location_data)} restaurants at coordinates ({coords['latitude']}, {coords['longitude']})")
                
                # Respect rate limits with 3 second delay
                time.sleep(1)
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            
            # Drop duplicate rows based on restaurant ID
            df = df.drop_duplicates(subset=['restaurantId'], keep='first')
            
            logging.info(f"Loaded {len(df)} unique restaurants from Opentable")
            
            return df
            
        except Exception as e:
            logging.error(f"Error loading Opentable data: {str(e)}")
            raise
    

    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate the scraped business data.
        
        Args:
            data (pd.DataFrame): DataFrame to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        required_columns = ['name', 'rating', 'review_count', 'address', 'categories', 'cluster_id']
        return all(col in data.columns for col in required_columns)
    
    def _scrape_location(self, latitude: float, longitude: float, page: int=1) -> List[Dict]:
        """
        Scrape a single page of results for a location.
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            page (int): Page number to scrape
            
        Returns:
            List[Dict]: List of business data
        """
        # Calculate next Saturday
        today = datetime.now()
        days_until_saturday = (5 - today.weekday()) % 7  # 5 is Saturday
        if days_until_saturday == 0:  # If today is Saturday, get next Saturday
            days_until_saturday = 7
        next_saturday = today.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_saturday)
        
        # Format date and time for URL (YYYYMMDDTHHMM)
        datetime_string = f"{next_saturday.strftime('%Y%m%d')}T2100"
        
        url = f"https://www.opentable.com/s?currentview=list&latitude={latitude}&longitude={longitude}&dateTime={datetime_string}&sortBy=distance"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
        logging.info(f"Scraping URL: {url}")
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        all_restaurants_data = []

        script_tags = soup.find_all("script", attrs={"type": "application/json"})
        for tag in script_tags:
            try:
                json_text = tag.string or tag.get_text()
                #json_text = tag.stringJ
                data = json.loads(json_text)
                
                restaurants = data['windowVariables']['__INITIAL_STATE__']['multiSearch']['restaurants']
                if isinstance(restaurants, list) and len(restaurants) > 0:
                    cleaned_restaurants = self._parse_business_listing(restaurants)
                    if cleaned_restaurants:
                            all_restaurants_data.extend(cleaned_restaurants)
            except Exception as e:
                logging.warning(f"Error parsing script tag: {str(e)}")
                continue
    
        return all_restaurants_data
    
    def _parse_business_listing(self, listing: List[Dict]) -> List[Dict]:
        """
        Parse a list of business listings from the search results.
        
        Args:
            listing (List[Dict]): List of restaurant data
            
        Returns:
            List[Dict]: List of parsed business data
        """
        clean_data = []
        try:
            for item in listing:
                try:
                    features_dict = item.get("features", {})
                    features_list = [key for key, val in features_dict.items() if isinstance(val, bool) and val]

                    restaurant = {
                        "restaurantId": item.get("restaurantId"),
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "profileLink": item.get("urls", {}).get("profileLink", {}).get("link"),
                        "priceBand": item.get("priceBand", {}).get("name"),
                        "currencySymbol": item.get("priceBand", {}).get("currencySymbol"),
                        "neighborhood": item.get("neighborhood", {}).get("name"),
                        "recentReservations": item.get("statistics", {}).get("recentReservationCount"),
                        "reviewCount": item.get("statistics", {}).get("reviews", {}).get("allTimeTextReviewCount"),
                        "rating": item.get("statistics", {}).get("reviews", {}).get("ratings", {}).get("overall", {}).get("rating"),
                        "primaryCuisine": item.get("primaryCuisine", {}).get("name"),
                        "isPromoted": item.get("isPromoted"),
                        "features": features_list,
                        "diningStyle": item.get("diningStyle"),
                        "latitude": item.get("coordinates", {}).get("latitude"),
                        "longitude": item.get("coordinates", {}).get("longitude"),
                        "address_line1": item.get("address", {}).get("line1"),
                        "address_line2": item.get("address", {}).get("line2"),
                        "city": item.get("address", {}).get("city"),
                        "state": item.get("address", {}).get("state"),
                        "postcode": item.get("address", {}).get("postCode"),
                        "description": item.get("description"),
                        "topReview": item.get("topReview", {}).get("highlightedText"),
                        "hasTakeout": item.get("hasTakeout"),
                        "phone": item.get("contactInformation", {}).get("formattedPhoneNumber")
                    }

                    clean_data.append(restaurant)

                
                except Exception as e:
                    logging.warning(f"Error parsing restaurant item: {str(e)}")
                    continue
                
            return clean_data
        except Exception as e:
            logging.error(f"Error parsing business listings: {str(e)}")
            return []

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the scraped data.
        
        Returns:
            Dict[str, Any]: Metadata about the scraped data
        """
        metadata = super().get_metadata()
        metadata.update({
            'centroids_file': str(self.centroids_file.absolute()),
            'n_clusters': len(self.centroids)
        })
        return metadata