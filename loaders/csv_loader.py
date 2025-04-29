"""
CSV data loader implementation for zoning data.
"""
import pandas as pd
from typing import Dict, Any, Optional
import logging
from pathlib import Path
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
        
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the loaded CSV data.
        
        Returns:
            Dict[str, Any]: Metadata about the loaded data
        """
        metadata = super().get_metadata()
        metadata.update({
            'zoning_file': str(Path(self.zoning_file).absolute())
        })
        return metadata 