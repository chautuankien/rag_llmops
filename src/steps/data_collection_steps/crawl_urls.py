from urllib.parse import urlparse

from tqdm import tqdm
from zenml import step, get_step_context
from typing_extensions import Annotated
from pydantic import BaseModel

from loguru import logger
from src.rag_chatbot.crawler_dispatcher.dispatcher import CrawlerDispatcher

@step()
def crawl_urls(urls: list[str]) -> Annotated[list[BaseModel], "crawled_urls"]:
    dispatcher = CrawlerDispatcher.build().register_notion()

    logger.info(f"Starting to crawl {len(urls)} url(s).")

    metadata = {}
    docs = []
    successfull_crawls = 0
    for url in tqdm(urls):
        successfull_crawl, crawled_domain, doc = _crawl_url(dispatcher, url)
        successfull_crawls += successfull_crawl

        docs.extend(doc)
        metadata = _add_to_metadata(metadata, crawled_domain, successfull_crawl)
    
    step_context = get_step_context()
    step_context.add_output_metadata(output_name="crawled_urls", metadata=metadata)

    logger.info(f"Successfully crawled {successfull_crawls} / {len(urls)} urls.")

    return docs

def _crawl_url(dispatcher: CrawlerDispatcher, url: str) -> tuple[bool, str, BaseModel | None]:
    crawler = dispatcher.get_crawler(url)
    crawler_domain = urlparse(url).netloc

    try:
        doc = crawler.extract(url=url)

        return (True, crawler_domain, doc)
    except Exception as e:
        logger.error(f"An error occurred while crawling: {e!s}")

        return (False, crawler_domain, None)

def _add_to_metadata(metadata: dict, domain: str, successfull_crawl: bool) -> dict:
    if domain not in metadata:
        metadata[domain] = {}
    metadata[domain]["successful"] = metadata.get(domain, {}).get("successful", 0) + successfull_crawl
    metadata[domain]["total"] = metadata.get(domain, {}).get("total", 0) + 1

    return metadata

if __name__ == "__main__":
    urls = ["https://maximelabonne.substack.com/p/uncensor-any-llm-with-abliteration-d30148b7d43e_link"]

    crawled_docs = crawl_urls(urls)