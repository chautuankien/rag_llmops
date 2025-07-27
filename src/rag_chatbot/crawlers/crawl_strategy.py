from loguru import logger
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer

class CrawlingStrategy(ABC):
    @abstractmethod
    def fetchContent(self, url: str) -> Dict[str, Any]: ...


class SeleniumStrategy(CrawlingStrategy):
    """
    Strategy that uses Selenium for web scraping.
    """
    def fetchContent(self, url: str) -> Dict[str, Any]:
        """
        Fetch content using Selenium.
        
        Args:
            url: The URL to fetch content from
            
        Returns:
            Dictionary containing the fetched content and metadata
        """
        # Implementation would use Selenium to navigate to the URL and extract content
        # This is a placeholder implementation
        return {
            "content": "Placeholder content fetched with Selenium",
            "metadata": {"fetch_method": "selenium"}
        }


class AsyncHtmlStrategy(CrawlingStrategy):
    """
    Strategy that uses asynchronous HTML requests for web scraping.
    """
    def fetchContent(self, url: str) -> Dict[str, Any]:
        """
        Fetch content using asynchronous HTML requests.
        
        Args:
            url: The URL to fetch content from
            
        Returns:
            Dictionary containing the fetched content and metadata
        """
        # Implementation would use async libraries like aiohttp to fetch content
        # This is a placeholder implementation

        loader = AsyncHtmlLoader(url)
        docs = loader.load()

        logger.info(f"Loaded {len(docs)} documents from {url}")

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        doc_transformed = docs_transformed[0]

        

        content = {
            "Title": doc_transformed.metadata.get("title", ""),
            "Subtitle": doc_transformed.metadata.get("subtitle", ""),
            "Content": doc_transformed.page_content,
            "Language": doc_transformed.metadata.get("language", ""),
        }

        return content