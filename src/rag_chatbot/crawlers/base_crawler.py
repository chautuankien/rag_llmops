from abc import ABC, abstractmethod
from pydantic import BaseModel

from src.rag_chatbot.domain.document import Document
from ..crawl_strategy.base_crawl_strategy import CrawlingStrategy

class BaseCrawler(ABC):
    def __init__(self, strategy: CrawlingStrategy):
        self.strategy = strategy
    
    # @abstractmethod
    # def _createDoc(self) -> Document: ...
    
    @abstractmethod
    def extract(self, url: str, **kwargs) -> Document: ...
