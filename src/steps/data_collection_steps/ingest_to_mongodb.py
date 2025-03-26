import os
from pydantic import BaseModel
from typing_extensions import Annotated
from zenml import step, get_step_context

from src.logger.logger import logger
from src.rag_chatbot.domain.document import Document
from src.rag_chatbot.infrastructure.mongodb.service import MongoDBService

@step
def ingest_to_mongodb(
    docs: list[BaseModel], 
    connection_string: str | None,
    collection_name: str,
    database_name: str,
    clear_collection: bool
    ) -> Annotated[int, "output"]:

    try:
        logger.info("Start ingesting documents to MongoDB")

        # Set connection string from param or env var
        connection_string = connection_string or os.environ.get("MONGODB_URI")
        if not connection_string:
            raise ValueError("MongoDB connection string must be provided or set as MONGODB_URI environment variable")
        
        doc_type = type(docs[0])
        with MongoDBService(model=doc_type,
                            mongodb_uri=connection_string, 
                            collection_name=collection_name,
                            database_name=database_name) as service:
            if clear_collection:
                logger.warning(
                    f"'clear_collection' is set to True. Clearing MongoDB collection '{collection_name}' before ingestion."
                )
                service.clear_collection()
            service.ingest_documents(docs)

            count = service.get_collection_count()
            logger.info(
                f"Successfully ingested {count} documents into MongoDB collection '{collection_name}'"
            )
        
        step_context = get_step_context()
        step_context.add_output_metadata(
            output_name="output",
            metadata={
                "count": count,
            },
        )

    return count