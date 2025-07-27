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