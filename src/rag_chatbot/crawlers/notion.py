from loguru import logger

from.base_crawler import BaseCrawler
from src.rag_chatbot.domain.document import Document, NotionDocument, NotionDocumentMetadata
from ..crawl_strategy.base_crawl_strategy import NotionStrategy

class NotionCrawler(BaseCrawler):
    """
    Crawler specifically designed for Notion documents.
    """
    def __init__(self):
        super().__init__(NotionStrategy())
    
    def extract(self, database_id: str) -> list[NotionDocument]:
        pass