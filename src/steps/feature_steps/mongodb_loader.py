import os
import json
import logging
import glob
from typing import Any, Optional
from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError, DuplicateKeyError
from dotenv import load_dotenv

from zenml.steps import step

from loguru import logger

@step
def load_chunks_into_mongodb(chunks: list[dict[str, Any]],
            connection_string: str | None = None,
            database_name: str = "document_store",
            collection_name: str = "embeddings"
            ) -> None:
    """
    Connect to MongoDB and setup the collection with proper indexes.
    """
    if not chunks:
        return 

    try:
        # Set connection string from param or env var
        connection_string = connection_string or os.environ.get("MONGODB_URI")
        if not connection_string:
            raise ValueError("MongoDB connection string must be provided or set as MONGODB_URI environment variable")
        
        client = MongoClient(connection_string)
        db = client[database_name]
        collection = db[collection_name]
        
        # Create indexes
        collection.create_index([("chunk_id", ASCENDING)], unique=True)
        collection.create_index([("document_url", ASCENDING)])
        
        # Test connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {database_name}.{collection_name}")

        # Prepare documents for insert
        for chunk in chunks:
            # Set _id to chunk_id for deduplication
            chunk["_id"] = chunk["chunk_id"]
        
        # Use bulk insert for better performance
        result = collection.insert_many(chunks, ordered=False)

        client.close()
        logger.info("MongoDB connection closed")
        
    except BulkWriteError as bwe:
        # Handle partial success in bulk write operations
        if hasattr(bwe, 'details') and 'nInserted' in bwe.details:
            inserted_count = bwe.details['nInserted']
            logger.warning(f"Partial insert: {inserted_count}/{len(chunks)} chunks inserted. Some chunks were duplicates.")
        else:
            logger.error(f"Bulk write error: {str(bwe)}")
    
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

@step
def close(client) -> None:
    """
    Close the MongoDB connection.
    """
    client.close()
    logger.info("MongoDB connection closed")

@step
def load_chunks(chunks: list[dict[str, Any]],
                collection
                ) -> int:
    """
    Load chunks into MongoDB.
    
    Args:
        chunks (list[dict]): List of chunks with embeddings
        
    Returns:
        int: Number of chunks successfully loaded
    """
    if not chunks:
        return 0
    
    inserted_count = 0
    
    try:
        # Prepare documents for insert
        for chunk in chunks:
            # Set _id to chunk_id for deduplication
            chunk["_id"] = chunk["chunk_id"]
        
        # Use bulk insert for better performance
        result = collection.insert_many(chunks, ordered=False)
        inserted_count = len(result.inserted_ids)
        
        logger.info(f"Inserted {inserted_count} documents into MongoDB")
        
    except BulkWriteError as bwe:
        # Handle partial success in bulk write operations
        if hasattr(bwe, 'details') and 'nInserted' in bwe.details:
            inserted_count = bwe.details['nInserted']
            logger.warning(f"Partial insert: {inserted_count}/{len(chunks)} chunks inserted. Some chunks were duplicates.")
        else:
            logger.error(f"Bulk write error: {str(bwe)}")
            
    except Exception as e:
        logger.error(f"Error inserting chunks into MongoDB: {str(e)}")
    
    return inserted_count


# Example usage
if __name__ == "__main__":
    # Set connection string in environment variable or pass directly
    # os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"

    load_dotenv()
    
    loader = MongoDBLoader()
    results = loader.load_all_embedded_files()
    
    total_loaded = sum(results.values())
    print(f"Loaded {total_loaded} documents from {len(results)} files")