from zenml import pipeline

from loguru import logger
from src.steps.data_collection_steps import (
    crawl_urls,
    ingest_to_mongodb
)

@pipeline
def etl(
    inputs: list[str]
) -> None:
    logger.info("----Start ETL pipeline----")

    docs = crawl_urls.crawl_urls(urls=inputs)

    ingest_to_mongodb.ingest_to_mongodb(
        docs=docs,
        clear_collection=True
    )

    logger.info("----End ETL pipeline----")

if __name__ == "__main__":
    urls = [
        "https://maximelabonne.substack.com/p/uncensor-any-llm-with-abliteration-d30148b7d43e_link",
        "https://www.notion.so/23d6c88a5848811b88d8fb1a5028e5b1?v=23d6c88a584881f0b46d000cdcadad31&source=copy_link"
    ]

    docs = crawl_urls.crawl_urls(urls=urls)

    ingest_to_mongodb.ingest_to_mongodb(
        docs=docs,
        clear_collection=True
    ) 