"""
Base loader class that defines the interface for all data loaders.
"""
from typing import Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

class BaseLoader(ABC):
    """
    Abstract base class for all data loaders.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the loader with configuration.
        
        Args:
            config (Dict[str, Any], optional): Override default configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def load_data(self) -> Any:
        """
        Load data from the source.
        
        Returns:
            Any: Loaded data (typically a DataFrame)
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """
        Validate the loaded data.
        
        Args:
            data (Any): Data to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the loaded data.
        
        Returns:
            Dict[str, Any]: Metadata about the loaded data
        """
        return {
            'loader_type': self.__class__.__name__,
            'config': self.config
        } 