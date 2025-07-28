from loguru import logger
import re

from.base_crawler import BaseCrawler
from src.rag_chatbot.infrastructure.notion import NotionClient, NotionPageClient
from src.rag_chatbot.domain.document import Document, NotionDocument, NotionDocumentMetadata
# from ..crawl_strategy.base_crawl_strategy import NotionStrategy

class NotionCrawler(BaseCrawler):
    """
    Crawler specifically designed for Notion documents.
    """
    def __init__(self):
        super().__init__()
        self.notion_client = NotionClient()
        self.page_client = NotionPageClient()

    def extract(self, url: str) -> list[Document]:
        """
        Extract content from a Notion database.
        
        Args:
            url: The ID of the Notion database to extract from
            **kwargs: Additional parameters for extraction
            
        Returns:
            List[NotionDocument]: List of extracted Notion documents
        """
        # Extract the Notion ID from the URL
        database_id = self._extract_notion_id(url)
        logger.info(f"Starting extraction from Notion database: {database_id}")
        
        try:
            # Step 1: Query the database to get metadata for all pages
            documents_metadata = self.notion_client.query_notion_database(database_id)
            logger.info(f"Found {len(documents_metadata)} documents in database {database_id}")

            if not documents_metadata:
                logger.warning(f"No documents found in database {database_id}")
                return []
            
            # Step 2: Extract content from each page
            documents = []
            for metadata in documents_metadata:
                try:
                    logger.debug(f"Extracting content from page: {metadata.title} (ID: {metadata.id})")
                    document = self.page_client.extract_document(metadata)
                    documents.append(document)
                    logger.debug(f"Successfully extracted content from page: {metadata.title}")
                    
                except Exception as e:
                    logger.error(f"Failed to extract content from page {metadata.id} ({metadata.title}): {e}")
                    # Continue with other documents even if one fails
                    continue

            logger.info(f"Successfully extracted {len(documents)} documents from database {database_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to extract from Notion database {database_id}: {e}")
            raise
    
    def _extract_notion_id(self, url: str) -> str:
        """
        Extract the Notion ID from a given URL.
        
        Args:
            url: The URL of the Notion page or database.
        
        Returns:
            str: The extracted Notion ID.
        """
        # Remove protocol and www prefix
        clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "")

        # Extract the 32-character hex ID from notion.so URLs
        # Pattern matches 32 consecutive hex characters
        pattern = r'([a-f0-9]{32})'
        match = re.search(pattern, clean_url) 
        if match:
            return match.group(1)         
        # If no match found, raise an error
        raise ValueError(f"Could not extract Notion ID from URL: {url}")