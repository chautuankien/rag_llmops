from zenml import pipeline

from src.logger.logger import logger
from src.steps.data_collection_steps import (
    crawl_urls,
    ingest_to_mongodb
)

@pipeline
def etl(
    input: list[str],
    connection_string: str | None,
    collection_name: str,
    database_name: str,
) -> None:
    logger.info("----Start ETL pipeline----")

    docs = crawl_urls.crawl_urls(urls=input)

    ingest_to_mongodb.ingest_to_mongodb(
        docs=docs,
        connection_string=connection_string,
        collection_name=collection_name,
        database_name=database_name,
        clear_collection=True
    )

    logger.info("----End ETL pipeline----")