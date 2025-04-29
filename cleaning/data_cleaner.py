"""
Data cleaning and transformation module.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union
import logging
from config import settings

class DataCleaner:
    """
    Class for cleaning and transforming data from various sources.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the data cleaner with configuration.
        
        Args:
            config (Dict[str, Any], optional): Override default configuration
        """
        self.config = config or {}
        self.clean_threshold = settings.PROCESSING['clean_threshold']
    
    def clean_data(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
        """
        Clean and transform data from any source.
        
        Args:
            data (Union[pd.DataFrame, Dict[str, pd.DataFrame]]): Input data to clean
            
        Returns:
            pd.DataFrame: Cleaned and transformed data
        """
        if isinstance(data, dict):
            # Handle multiple DataFrames (e.g., from CSVLoader)
            return self._clean_multiple_sources(data)
        else:
            # Handle single DataFrame (e.g., from FoursquareLoader or YelpScraper)
            return self._clean_single_source(data)
    
    def _clean_multiple_sources(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Clean and merge data from multiple sources.
        
        Args:
            data_dict (Dict[str, pd.DataFrame]): Dictionary of DataFrames to clean
            
        Returns:
            pd.DataFrame: Cleaned and merged data
        """
        cleaned_data = {}
        
        for source, df in data_dict.items():
            try:
                cleaned_data[source] = self._clean_single_source(df)
            except Exception as e:
                logging.error(f"Error cleaning {source} data: {str(e)}")
                continue
        
        # Merge cleaned DataFrames based on common columns
        if 'zoning' in cleaned_data and 'permits' in cleaned_data:
            return self._merge_zoning_permits(
                cleaned_data['zoning'],
                cleaned_data['permits']
            )
        else:
            return pd.concat(cleaned_data.values(), ignore_index=True)
    
    def _clean_single_source(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a single DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame to clean
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Standardize column names
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Convert data types
        df = self._convert_data_types(df)
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in the DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame with missing values
            
        Returns:
            pd.DataFrame: DataFrame with handled missing values
        """
        # Calculate completeness ratio for each row
        completeness = df.notna().mean(axis=1)
        
        # Filter rows based on completeness threshold
        df = df[completeness >= self.clean_threshold]
        
        # Fill remaining missing values based on data type
        for column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].fillna('unknown')
            elif pd.api.types.is_numeric_dtype(df[column]):
                df[column] = df[column].fillna(df[column].median())
            elif pd.api.types.is_datetime64_dtype(df[column]):
                df[column] = df[column].fillna(pd.NaT)
        
        return df
    
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert DataFrame columns to appropriate data types.
        
        Args:
            df (pd.DataFrame): DataFrame to convert
            
        Returns:
            pd.DataFrame: DataFrame with converted data types
        """
        # Identify and convert numeric columns
        for column in df.columns:
            try:
                # Try to convert to numeric
                if df[column].dtype == 'object':
                    df[column] = pd.to_numeric(df[column], errors='ignore')
                    
                # Convert boolean-like columns
                if df[column].dtype == 'object':
                    if df[column].isin(['true', 'false', 'True', 'False']).all():
                        df[column] = df[column].map({'true': True, 'false': False,
                                                   'True': True, 'False': False})
            except Exception as e:
                logging.debug(f"Could not convert column {column}: {str(e)}")
                continue
                
        return df
    
    def _merge_zoning_permits(self, zoning_df: pd.DataFrame, permits_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge zoning and permits data based on location.
        
        Args:
            zoning_df (pd.DataFrame): Zoning data
            permits_df (pd.DataFrame): Permits data
            
        Returns:
            pd.DataFrame: Merged DataFrame
        """
        # Ensure location columns exist
        if not all(col in zoning_df.columns for col in ['latitude', 'longitude']):
            raise ValueError("Zoning data missing location columns")
            
        # Convert addresses to coordinates if needed
        if 'latitude' not in permits_df.columns:
            permits_df = self._geocode_addresses(permits_df)
            
        # Merge based on nearest coordinates
        merged_df = pd.merge_asof(
            permits_df.sort_values('latitude'),
            zoning_df.sort_values('latitude'),
            on='latitude',
            by='longitude',
            tolerance=0.001  # ~100m tolerance
        )
        
        return merged_df
    
    def _geocode_addresses(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert addresses to coordinates using a geocoding service.
        This is a placeholder - implement actual geocoding logic.
        
        Args:
            df (pd.DataFrame): DataFrame with addresses
            
        Returns:
            pd.DataFrame: DataFrame with added coordinates
        """
        # TODO: Implement actual geocoding using a service like Google Maps or Nominatim
        logging.warning("Geocoding not implemented - returning original DataFrame")
        return df 