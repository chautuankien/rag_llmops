import os
import time
from dotenv import load_dotenv

from zenml import pipeline

# Import the modules
from src.logger.logger import logger
from src.steps.feature_steps.fetch_from_mongodb import fetch_from_mongodb
from src.steps.feature_steps.data_extraction import data_extraction
from src.steps.feature_steps.chunking import chunk_documents
from src.steps.feature_steps.embedding import embed_chunks
from src.steps.feature_steps.mongodb_loader import load_chunks_into_mongodb

load_dotenv()

@pipeline
def feature_pipeline(urls: list[str], 
                     process_delay: int = 1, 
                     base_output_dir: str = "pipeline_outputs/feature_pipeline_output"
                     ) -> None:
    """
    Run the complete feature pipeline from crawling to MongoDB loading.
    
    Args:
        urls (List[str]): List of URLs to process
        process_delay (int): Delay between URL processing in seconds
        
    Returns:
        Dict[str, Any]: Pipeline statistics
    """
    start_time = time.time()

    # Setup credentials from params or env vars
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    mongodb_uri = os.environ.get("MONGODB_URI")

    # Setup output directories
    base_output_dir = base_output_dir
    crawled_dir = os.path.join(base_output_dir, "crawled_data")
    chunked_dir = os.path.join(base_output_dir, "chunked_data")
    embedded_dir = os.path.join(base_output_dir, "embedded_data")
    
    # Create directories
    for dir_path in [crawled_dir, chunked_dir, embedded_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Step 1: Fetch documents from MongoDB
    logger.info(f"🔄 STEP 1: Fetching documents from MongoDB")
    documents = fetch_from_mongodb(limit=5)


    # Step 2: Extract data from URLs
    logger.info(f"🔄 STEP 2: Extracting data from {len(documents)} fetched documents")
    extracted_docs = data_extraction(urls, delay=process_delay, output_dir=crawled_dir)
    
    if not extracted_docs:
        logger.warning("No documents extracted. Pipeline stopping.")
        return 
    
    # Step 2: Chunk the documents
    # logger.info(f"🔄 STEP 2: Chunking {len(extracted_docs)} documents")
    logger.info(f"🔄 STEP 2: Chunking documents")
    chunks = chunk_documents(extracted_docs)
    
    if not chunks:
        logger.warning("No chunks created. Pipeline stopping.")
        return
    
    # Step 3: Generate embeddings for chunks
    # logger.info(f"🔄 STEP 3: Generating embeddings for {len(chunks)} chunks")
    logger.info(f"🔄 STEP 3: Generating embeddings for chunks")
    embedded_chunks = embed_chunks(chunks=chunks, 
                                   api_key=openai_api_key, 
                                   model = "text-embedding-3-small", 
                                   batch_size = 20,
                                   output_dir = embedded_dir)
    
    if not embedded_chunks:
        logger.warning("No embeddings generated. Pipeline stopping.")
        return

    
    # Step 4: Load embeddings into MongoDB
    # logger.info(f"🔄 STEP 4: Loading {len(embedded_chunks)} embeddings into MongoDB")
    logger.info(f"🔄 STEP 4: Loading embeddings into MongoDB")
    load_chunks_into_mongodb(embedded_chunks, connection_string=mongodb_uri)
    
    # Calculate total processing time
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"✅ Pipeline completed in {total_time:.2f} seconds")
        

if __name__ == "__main__":
    load_dotenv()

    # Setup pipeline
    urls = [
        "https://docs.zenml.io/getting-started/installation",
        "https://docs.zenml.io/"
    ]
    stats = feature_pipeline(urls)
    
    # print(f"Pipeline completed. Statistics: {stats}")