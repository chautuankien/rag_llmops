from urllib.parse import urlparse

from loguru import logger
from .base_crawler import BaseCrawler
from src.rag_chatbot.domain.document import Document, ArticleDocument
from ..crawl_strategy.base_crawl_strategy import AsyncHtmlStrategy

class CustomArticleCrawler(BaseCrawler):
    """
    Crawler for custom article sources.
    """
    def __init__(self):
        super().__init__(AsyncHtmlStrategy())
    
    def extract(self, url: str, **kwargs) -> Document:
        """
        Extract content from a custom article.
        
        Args:
            url: The URL of the custom article
            **kwargs: Additional parameters for extraction
        """
        logger.info(f"Starting scrapping article: {url}")
        content = self.strategy.fetchContent(url)

        parsed_url = urlparse(url)  # breakdown url into sub-components (scheme, netloc, path, etc)
        platform = parsed_url.netloc        # get only domain part

        logger.info(f"Successfully scraped article: {url}")
        
        return ArticleDocument(
            url=url,
            platform=platform,
            content=content,  
        )
            