from typing import Generic, Type, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pymongo import MongoClient, errors

from loguru import logger
from src.settings import settings

T = TypeVar("T", bound=BaseModel)


class MongoDBService(Generic[T]):
    """Service class for MongoDB operations, supporting ingestion, querying, and validation.

    This class provides methods to interact with MongoDB collections, including document
    ingestion, querying, and validation operations.

    Args:
        model: The Pydantic model class to use for document serialization.
        collection_name: Name of the MongoDB collection to use.
        database_name: Name of the MongoDB database to use.
        mongodb_uri: URI for connecting to MongoDB instance.

    Attributes:
        model: The Pydantic model class used for document serialization.
        collection_name: Name of the MongoDB collection.
        database_name: Name of the MongoDB database.
        mongodb_uri: MongoDB connection URI.
        client: MongoDB client instance for database connections.
        database: Reference to the target MongoDB database.
        collection: Reference to the target MongoDB collection.
    """

    def __init__(
        self,
        model: dict[str, Type[T]] | None = None,
        mongodb_uri: str = settings.MONGODB_URI,
        database_name: str = settings.MONGODB_DATABASE_NAME,
        collection_name: str = settings.MONGODB_COLLECTION_NAME
        
    ) -> None:
        """Initialize a connection to the MongoDB collection.

        Args:
            collection_name: Name of the MongoDB collection to use.
            model_class: The Pydantic model class to use for document serialization.
            database_name: Name of the MongoDB database to use.
                Defaults to value from settings.
            mongodb_uri: URI for connecting to MongoDB instance.
                Defaults to value from settings.

        Raises:
            Exception: If connection to MongoDB fails.
        """

        self.model = model
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.collection_name = collection_name

        try:
            self.client = MongoClient(mongodb_uri, appname="rag_llmops")
            self.client.admin.command("ping")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDBService: {e}")
            raise

        self.database = self.client[database_name]
        self.collection = self.database[collection_name]
        logger.info(
            f"Connected to MongoDB instance:\n URI: {mongodb_uri}\n Database: {database_name}\n Collection: {collection_name}"
        )

    def __enter__(self) -> "MongoDBService":
        """Enable context manager support.

        Returns:
            MongoDBService: The current instance.
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close MongoDB connection when exiting context.

        Args:
            exc_type: Type of exception that occurred, if any.
            exc_val: Exception instance that occurred, if any.
            exc_tb: Traceback of exception that occurred, if any.
        """

        self.close()

    def clear_collection(self) -> None:
        """Remove all documents from the collection.

        This method deletes all documents in the collection to avoid duplicates
        during reingestion.

        Raises:
            errors.PyMongoError: If the deletion operation fails.
        """

        try:
            result = self.collection.delete_many({})
            logger.debug(
                f"Cleared collection. Deleted {result.deleted_count} documents."
            )
        except errors.PyMongoError as e:
            logger.error(f"Error clearing the collection: {e}")
            raise

    def ingest_documents(self, documents: list[T]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            documents: List of Pydantic model instances to insert.

        Raises:
            ValueError: If documents is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """

        try:
            if not documents or not all(
                isinstance(doc, BaseModel) for doc in documents
            ):
                raise ValueError("Documents must be a list of Pydantic models.")

            dict_documents = [doc.model_dump() for doc in documents]

            # Remove '_id' fields to avoid duplicate key errors
            for doc in dict_documents:
                doc.pop("_id", None)

            self.collection.insert_many(dict_documents)
            logger.debug(f"Inserted {len(documents)} documents into MongoDB.")
        except errors.PyMongoError as e:
            logger.error(f"Error inserting documents: {e}")
            raise

    def fetch_documents(self, limit: int, query: dict) -> list[T]:
        """Retrieve documents from the MongoDB collection based on a query.

        Args:
            limit: Maximum number of documents to retrieve.
            query: MongoDB query filter to apply.

        Returns:
            List of Pydantic model instances matching the query criteria.

        Raises:
            Exception: If the query operation fails.
        """
        try:
            # Execute the MongoDB query with the provided filter and limit
            # .find(query) creates a cursor that matches documents based on the query dictionary
            # .limit(limit) restricts the number of documents returned to prevent memory issues
            documents = list(self.collection.find(query).limit(limit))
            logger.debug(f"Fetched {len(documents)} documents with query: {query}")
            return self._parse_documents(documents)
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            raise

    def _parse_documents(self, documents: list[dict]) -> list[T]:
        """Convert MongoDB documents to Pydantic model instances.

        Converts MongoDB ObjectId fields to strings and transforms the document structure
        to match the Pydantic model schema.

        Args:
            documents: List of MongoDB documents to parse.

        Returns:
            List of validated Pydantic model instances.
        """
        parsed_documents = []
        # Iterate through each document (dictionary) returned from MongoDB
        for doc in documents:
            for key, value in doc.items():
                # Check if the value is a MongoDB ObjectId
                # ObjectId is a special BSON type that needs to be converted to string
                # because Pydantic models expect string IDs, not ObjectId objects
                if isinstance(value, ObjectId):
                    doc[key] = str(value)

            # Remove the MongoDB '_id' field from the document
            # MongoDB uses '_id' as the primary key, but our Pydantic model uses 'id'
            # .pop() removes and returns the value, or None if the key doesn't exist
            _id = doc.pop("_id", None)

            # Add the '_id' value back as 'id' to match our Pydantic model schema
            doc["id"] = _id

            # Create a Pydantic model instance from the modified document
            # .model_validate() performs:
            # 1. Type checking and conversion
            # 2. Data validation according to the model schema
            # 3. Returns a fully validated Pydantic object
            # If validation fails, this will raise a ValidationError
            if doc.get("doc_type") == "NotionDocument":
                parsed_doc = self.model[doc.get("doc_type")].model_validate(doc)
            elif doc.get("doc_type") == "ArticleDocument":
                parsed_doc = self.model[doc.get("doc_type")].model_validate(doc)

            parsed_documents.append(parsed_doc)

        return parsed_documents

    def get_collection_count(self) -> int:
        """Count the total number of documents in the collection.

        Returns:
            Total number of documents in the collection.

        Raises:
            errors.PyMongoError: If the count operation fails.
        """

        try:
            return self.collection.count_documents({})
        except errors.PyMongoError as e:
            logger.error(f"Error counting documents in MongoDB: {e}")
            raise

    def close(self) -> None:
        """Close the MongoDB connection.

        This method should be called when the service is no longer needed
        to properly release resources, unless using the context manager.
        """

        self.client.close()
        logger.debug("Closed MongoDB connection.")

if __name__ == "__main__":
    # Example usage of MongoDBService
    from src.rag_chatbot.domain.document import NotionDocument, ArticleDocument

    model: dict = {
        "NotionDocument": NotionDocument,
        "ArticleDocument": ArticleDocument,
    }

    service = MongoDBService(model=model, 
                             collection_name=settings.MONGODB_COLLECTION_NAME)

    # Fetch documents with a limit of 10
    fetched_docs = service.fetch_documents(limit=10, query={})
    print(f"Fetched {len(fetched_docs)} documents.")

    # Close the service
    service.close()
