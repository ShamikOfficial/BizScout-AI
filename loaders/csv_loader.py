"""
CSV data loader implementation for zoning data.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import json
from geopy.geocoders import Nominatim
import shapely.wkt
from shapely.geometry import shape
from sklearn.cluster import KMeans
from .base_loader import BaseLoader
from config import settings

class CSVLoader(BaseLoader):
    """
    Loader for CSV data sources (zoning data).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CSV loader with configuration.
        
        Args:
            config (Dict[str, Any], optional): Override default configuration
        """
        super().__init__(config)
        self.zoning_file = settings.DATA_SOURCES['csv']['zoning_file']
        self.geolocator = Nominatim(user_agent="geocoding_app")
        self.n_clusters = config.get('n_clusters', 1000) if config else 1000
        self.centroids_file = Path(settings.DATA_DIR) / 'semi_processed' / 'cluster_centroids.json'
    
    def get_zipcode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Get zipcode from latitude and longitude coordinates.
        
        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate
            
        Returns:
            Optional[str]: Zipcode if found, None otherwise
        """
        try:
            location = self.geolocator.reverse((latitude, longitude), exactly_one=True)
            if location:
                print(location.raw['address'].get('postcode'))
                return location.raw['address'].get('postcode')
        except Exception as e:
            logging.warning(f"Error getting zipcode for coordinates ({latitude}, {longitude}): {str(e)}")
        return None

    def _calculate_centroid(self, geometry_str: str) -> Optional[Dict[str, float]]:
        """
        Calculate centroid coordinates from WKT geometry string.
        
        Args:
            geometry_str (str): WKT geometry string
            
        Returns:
            Optional[Dict[str, float]]: Dictionary with latitude and longitude if successful, None otherwise
        """
        try:
            # Parse WKT geometry
            geom = shapely.wkt.loads(geometry_str)
            # Calculate centroid
            centroid = geom.centroid
            return {
                'latitude': centroid.y,  # Note: y is latitude in WKT
                'longitude': centroid.x  # Note: x is longitude in WKT
            }
        except Exception as e:
            logging.warning(f"Error calculating centroid: {str(e)}")
            return None

    def _perform_clustering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform KMeans clustering on the centroids, taking frequency into account.
        
        Args:
            df (pd.DataFrame): DataFrame with centroid coordinates
            
        Returns:
            pd.DataFrame: DataFrame with added cluster information
        """
        try:
            # Round coordinates to reduce noise
            df['lat_rounded'] = df['centroid_latitude'].round(4)
            df['long_rounded'] = df['centroid_longitude'].round(4)
            
            # Calculate frequency of each coordinate pair
            freq_df = df.groupby(['lat_rounded', 'long_rounded']).size().reset_index(name='frequency')
            
            # Use frequency as weights by repeating rows
            repeated_rows = freq_df.loc[freq_df.index.repeat(freq_df['frequency'])].reset_index(drop=True)
            coords = repeated_rows[['lat_rounded', 'long_rounded']].to_numpy()
            
            # KMeans clustering
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
            labels = kmeans.fit_predict(coords)
            
            # Assign cluster labels back to repeated rows
            repeated_rows['cluster'] = labels
            
            # Map cluster label back to original (lat_rounded, long_rounded)
            label_map = repeated_rows.groupby(['lat_rounded', 'long_rounded'])['cluster'].agg(
                lambda x: x.value_counts().idxmax()
            ).reset_index()
            
            # Create a mapping of cluster labels to their centroids
            cluster_centroids = pd.DataFrame(
                kmeans.cluster_centers_,
                columns=['centroid_lat', 'centroid_long']
            )
            cluster_centroids['cluster'] = range(len(cluster_centroids))
            
            # Merge cluster information back to original DataFrame
            df = df.merge(label_map, on=['lat_rounded', 'long_rounded'], how='left')
            
            # Add cluster centroids
            df = df.merge(cluster_centroids, on='cluster', how='left')
            
            # Create centroid_coord column
            df['centroid_coord'] = df.apply(
                lambda row: f"({row['centroid_lat']:.4f}, {row['centroid_long']:.4f})" 
                if pd.notnull(row['cluster']) else None,
                axis=1
            )
            
            # Drop temporary columns
            df.drop(['lat_rounded', 'long_rounded', 'centroid_lat', 'centroid_long'], axis=1, inplace=True)
            
            logging.info(f"Clustering completed. Created {self.n_clusters} clusters")
            return df
            
        except Exception as e:
            logging.error(f"Error performing clustering: {str(e)}")
            return df

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load zoning data.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary containing zoning dataset
        """
        try:
            zoning_data = self._load_zoning_data()
            
            return {
                'zoning': zoning_data
            }
        except Exception as e:
            logging.error(f"Error loading CSV data: {str(e)}")
            raise
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate the loaded CSV data.
        
        Args:
            data (pd.DataFrame): DataFrame to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        # Basic validation - check if DataFrame is not empty
        if data.empty:
            return False
            
        # Check for required columns
        required_columns = ['SHAPE_Len','SHAPE_Area','ZONE_CMPLT','the_geom']
        if not all(col in data.columns for col in required_columns):
            return False
            
        # Drop rows with empty ZONE_CMPLT
        data.dropna(subset=['ZONE_CMPLT'], inplace=True)
        
        return True
    
    def save_centroids(self, df: pd.DataFrame) -> None:
        """
        Save cluster centroids to a JSON file.
        
        Args:
            df (pd.DataFrame): DataFrame containing cluster centroids
        """
        try:
            # Extract unique centroids
            centroids = df[['cluster', 'centroid_coord']].drop_duplicates()
            centroids = centroids[centroids['cluster'] != -1]  # Remove noise points if any
            
            # Convert to dictionary format
            centroids_dict = {}
            for _, row in centroids.iterrows():
                # Parse the coordinate string
                coords = row['centroid_coord'].strip('()').split(',')
                centroids_dict[str(int(row['cluster']))] = {
                    'latitude': float(coords[0]),
                    'longitude': float(coords[1])
                }
            
            # Create directory if it doesn't exist
            self.centroids_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to JSON
            with open(self.centroids_file, 'w') as f:
                json.dump(centroids_dict, f, indent=2)
            
            logging.info(f"Saved {len(centroids_dict)} cluster centroids to {self.centroids_file}")
            
        except Exception as e:
            logging.error(f"Error saving centroids: {str(e)}")
            raise

    def _load_zoning_data(self) -> pd.DataFrame:
        """
        Load and process zoning data.
        
        Returns:
            pd.DataFrame: Processed zoning data
        """
        file_path = Path(self.zoning_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Zoning file not found: {self.zoning_file}")
            
        df = pd.read_csv(file_path)
        
        if not self.validate_data(df):
            raise ValueError("Invalid zoning data format")
        
        # Calculate centroids and add as separate columns
        centroids = df['the_geom'].apply(self._calculate_centroid)
        df['centroid_latitude'] = centroids.apply(lambda x: x['latitude'] if x is not None else None)
        df['centroid_longitude'] = centroids.apply(lambda x: x['longitude'] if x is not None else None)
        
        # Perform clustering on centroids
        df = self._perform_clustering(df)
        
        # Save centroids to JSON file
        self.save_centroids(df)
        
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the loaded CSV data.
        
        Returns:
            Dict[str, Any]: Metadata about the loaded data
        """
        metadata = super().get_metadata()
        metadata.update({
            'zoning_file': str(Path(self.zoning_file).absolute()),
            'n_clusters': self.n_clusters
        })
        return metadata 