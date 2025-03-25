from urllib.parse import urlparse

from tqdm import tqdm
from zenml import step, get_step_context
from typing_extensions import Annotated

from src.logger.logger import logger
from src.rag_chatbot.crawlers.dispatcher import CrawlerDispatcher

@step
def crawl_urls(urls: list[str]) -> Annotated[list[str], "crawled_urls"]:
    dispatcher = CrawlerDispatcher.build()

    logger.info(f"Starting to crawl {len(urls)} link(s).")
    successfull_crawls = 0

