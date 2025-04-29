"""
Web scraper implementation for Yelp business data.
"""
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_loader import BaseLoader
from config import settings
from datetime import datetime
import json

class OpentableScraper(BaseLoader):
    """
    Web scraper for Yelp business data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Opentable scraper with configuration.
        
        Args:
            config (Dict[str, Any], optional): Override default configuration
        """
        super().__init__(config)
        self.base_url = settings.DATA_SOURCES['opentable']['base_url']
        self.search_path = settings.DATA_SOURCES['opentable']['search_path']
        self.max_pages = settings.DATA_SOURCES['opentable']['max_pages']
        
    def load_data(self) -> pd.DataFrame:
        """
        Scrape business data from Opentable.
        
        Returns:
            pd.DataFrame: DataFrame containing business data
        """
        results = []
        location = settings.DEFAULT_LOCATION
        
        try:
            # # Initialize Selenium WebDriver (headless mode)
            # options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            # driver = webdriver.Chrome(options=options)
            
            # Scrape data for each page
            for page in range(self.max_pages):
                businesses = self._scrape_page(latitude=location['latitude'], longitude=location['longitude'], page=page)
                if not businesses:
                    break
                results.extend(businesses)
                time.sleep(5)
                
            #driver.quit()
            
            df = pd.DataFrame(results)
            df=df.astype('str') 
            # if self.validate_data(df):
            #     return df
            # else:
            #     raise ValueError("Invalid data scraped from Yelp")
            return df    
        except Exception as e:
            logging.error(f"Error scraping Yelp data: {str(e)}")
            raise
            
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate the scraped business data.
        
        Args:
            data (pd.DataFrame): DataFrame to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        required_columns = ['name', 'rating', 'review_count', 'address', 'categories']
        return all(col in data.columns for col in required_columns)
    
    def _scrape_page(self, latitude: float, longitude: float, page: int) -> List[Dict]:
        date_now = datetime.now().strftime("%Y%m%d")
        datetime_string = f"{date_now}T1900"

        url = f"https://www.opentable.com/s?currentview=list&datetime={datetime_string}&latitude={latitude}&longitude={longitude}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        all_restaurants_data = []

        script_tags = soup.find_all("script", attrs={"type": "application/json"})
        for tag in script_tags:
            try:
                json_text = tag.string
                data = json.loads(json_text)
                restaurants = data['windowVariables']['__INITIAL_STATE__']['multiSearch']['restaurants']
                if isinstance(restaurants, list) and len(restaurants) > 0:
                    cleaned_restraunts=self._parse_business_listing(restaurants)
                    if cleaned_restraunts:
                        all_restaurants_data.extend(cleaned_restraunts)
            except Exception:
                continue

        return all_restaurants_data
    
    def _parse_business_listing(self, listing: BeautifulSoup) -> List[Dict]:
        """
        Parse a single business listing from the search results.
        
        Args:
            listing (BeautifulSoup): HTML element containing business data
            
        Returns:
            Optional[Dict]: Parsed business data or None if parsing fails
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
                        # "orderOnlineLink" intentionally excluded
                    }

                    clean_data.append(restaurant)
                except Exception:
                    continue

            return clean_data
        except Exception as e:
            logging.debug(f"Error parsing business element: {str(e)}")
            return None