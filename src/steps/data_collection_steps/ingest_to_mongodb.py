from typing import Union
from zenml import step, get_step_context

from loguru import logger
from src.rag_chatbot.domain.document import Document, ArticleDocument, NotionDocument
from src.rag_chatbot.infrastructure.mongodb.service import MongoDBService

# Define the same union type
DocumentTypes = ArticleDocument | NotionDocument

@step
def ingest_to_mongodb(
    docs: list[list[DocumentTypes]], 
    clear_collection: bool
    ) -> None:
    
    logger.info("Start ingesting documents to MongoDB")

    # doc_type = type(docs[0][0])
    # with MongoDBService(model=doc_type) as service:
    with MongoDBService() as service:
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