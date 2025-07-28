from abc import ABC, abstractmethod
from pydantic import BaseModel

from src.rag_chatbot.domain.document import Document
# from ..crawl_strategy.base_crawl_strategy import CrawlingStrategy

class BaseCrawler(ABC):
    def __init__(self):
        """
        Base class for all crawlers.
        """
        super().__init__()
    
    # @abstractmethod
    # def _createDoc(self) -> Document: ...
    
    @abstractmethod
    def extract(self, inputs_data: list[str], **kwargs) -> list[Document]: ...
