from zenml import pipeline

from loguru import logger
from src.steps.data_collection_steps import (
    crawl_urls,
    add_quality_score,
    ingest_to_mongodb
)

@pipeline
def etl(
    inputs: list[str],
    quality_agent_model_id: str = "gpt-4o-mini",
    quality_agent_mock: bool = False,
    max_concurrent_requests: int = 5
) -> None:
    logger.info("----Start ETL pipeline----")

    crawled_docs = crawl_urls(urls=inputs)

    scored_docs = add_quality_score(
        documents=crawled_docs,
        model_id=quality_agent_model_id,
        mock=quality_agent_mock,
        max_concurrent_requests=max_concurrent_requests
    )

    ingest_to_mongodb(
        docs=scored_docs,
        clear_collection=True
    )

    logger.info("----End ETL pipeline----")

if __name__ == "__main__":
    urls = [
        "https://maximelabonne.substack.com/p/uncensor-any-llm-with-abliteration-d30148b7d43e_link",
        "https://www.notion.so/23d6c88a5848811b88d8fb1a5028e5b1?v=23d6c88a584881f0b46d000cdcadad31&source=copy_link"
    ]

    crawled_docs = crawl_urls(urls=urls)

    scored_docs = add_quality_score(documents=crawled_docs)

    ingest_to_mongodb(
        docs=scored_docs,
        clear_collection=True
    ) 