from abc import ABC, abstractmethod
from pydantic import BaseModel

from src.rag_chatbot.domain.document import Document
from .crawl_strategy import CrawlingStrategy

class BaseCrawler(ABC):
    def __init__(self, strategy: CrawlingStrategy):
        self.strategy = strategy
    
    # @abstractmethod
    # def _createDoc(self) -> Document: ...
    
    @abstractmethod
    def extract(self, url: str, **kwargs) -> Document: ...

    
    def handleError(self, e: Exception) -> None:
        """
        Handle exceptions that occur during extraction.
        
        Args:
            e: The exception that occurred
        """
        error_message = f"Error during extraction: {str(e)}"
        self.logError(error_message)
    
    def logError(self, msg: str) -> None:
        """
        Log error messages.
        
        Args:
            msg: The error message to log
        """
        # This would typically write to a log file or logging system
        print(f"ERROR: {msg}")