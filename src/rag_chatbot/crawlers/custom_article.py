from urllib.parse import urlparse
from loguru import logger
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers.html2text import Html2TextTransformer

from .base_crawler import BaseCrawler
from src.rag_chatbot.domain.document import Document, ArticleDocument
# from ..crawl_strategy.base_crawl_strategy import AsyncHtmlStrategy

class CustomArticleCrawler(BaseCrawler):
    """
    Crawler for blog sources.
    """
    def __init__(self):
        super().__init__()

    def extract(self, url: str, **kwargs) -> list[Document]:
        """
        Extract content from a custom article.
        
        Args:
            url: The URL of the custom article
            **kwargs: Additional parameters for extraction
        """
        logger.info(f"Starting scrapping article: {url}")
        loader = AsyncHtmlLoader(url)
        docs = loader.load()

        logger.info(f"Loaded {len(docs)} documents from {url}")

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        doc_transformed = docs_transformed[0]
        # content = self.strategy.fetchContent(url)

        parsed_url = urlparse(url)  # breakdown url into sub-components (scheme, netloc, path, etc)
        platform = parsed_url.netloc        # get only domain part

        extracted_docs = []
        doc = ArticleDocument(
            url=doc_transformed.metadata.get("source", ""),
            title=doc_transformed.metadata.get("title", ""),
            language=doc_transformed.metadata.get("language", ""),
            platform=platform,
            content=doc_transformed.page_content,
            doc_type="ArticleDocument"
        )
        extracted_docs.append(doc)
        logger.info(f"Successfully scraped article: {url}")

        return extracted_docs
