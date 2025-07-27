import os
from pydantic import BaseModel
from typing_extensions import Annotated
from zenml import step, get_step_context

from loguru import logger
from src.rag_chatbot.domain.document import Document
from src.rag_chatbot.infrastructure.mongodb.service import MongoDBService

@step
def ingest_to_mongodb(
    docs: list[BaseModel], 
    clear_collection: bool
    ) -> None:
  
    logger.info("Start ingesting documents to MongoDB")

    doc_type = type(docs[0])
    with MongoDBService(model=doc_type) as service:
        if clear_collection:
            logger.warning(
                f"'clear_collection' is set to True. Clearing MongoDB collection before ingestion."
            )
            service.clear_collection()

        service.ingest_documents(docs)

        count = service.get_collection_count()
        logger.info(
            f"Successfully ingested {count} documents into MongoDB collection"
        )