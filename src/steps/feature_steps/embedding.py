import os
import json
import time
from typing import Any
from typing_extensions import Annotated
from openai import OpenAI
import backoff
from dotenv import load_dotenv

from zenml.steps import step

from loguru import logger


@step
def embed_chunks(chunks: list[dict[str, Any]],
                api_key: str | None = None,
                model: str = "text-embedding-3-small",
                batch_size: int = 20,
                output_dir: str = "data/feature_pipeline_data/embedded_data"
                ) -> Annotated[list[dict[str, Any]], "embedded chunks"]:
    """
    Generate embeddings for a list of chunks.
    
    Args:
        chunks (list[Dict]): List of chunk dictionaries
        
    Returns:
        list[Dict]: Chunks with added embedding vectors
    """
    if not chunks:
        return []
    
    embedded_chunks = []
    chunk_batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    
    for i, batch in enumerate(chunk_batches):
        try:
            logger.info(f"Processing batch {i+1}/{len(chunk_batches)} ({len(batch)} chunks)")
            
            # Extract texts for embedding
            texts = [chunk["content"] for chunk in batch]
            
            # Get embeddings with exponential backoff for rate limiting
            embeddings = _get_embeddings_with_backoff(texts, api_key, model)
            
            # Add embeddings to chunks
            for j, chunk in enumerate(batch):
                chunk_with_embedding = chunk.copy()
                chunk_with_embedding["embedding"] = embeddings[j]
                embedded_chunks.append(chunk_with_embedding)
            
            # Save embedded chunks to file
            _save_embedded_chunks(embedded_chunks, output_dir)
            
            # Sleep to respect rate limits
            if i < len(chunk_batches) - 1:
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error embedding batch {i+1}: {str(e)}")
            # Still try to continue with next batch
    
    logger.info(f"Successfully embedded {len(embedded_chunks)}/{len(chunks)} chunks")
    return embedded_chunks

@backoff.on_exception(backoff.expo, 
                        (Exception),
                        max_tries=5)
def _get_embeddings_with_backoff(texts: list[str],
                                api_key: str,
                                model: str,
                                ) -> list[list[float]]:
    """
    Get embeddings with exponential backoff for API rate limiting.
    
    Args:
        texts (list[str]): List of texts to embed
        
    Returns:
        list[list[float]]: List of embedding vectors
    """
    try:
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        
        # Extract embedding data from response
        embeddings = [item.embedding for item in response.data]
        return embeddings
        
    except Exception as e:
        logger.warning(f"API error: {str(e)}. Retrying...")
        raise

def _save_embedded_chunks(embedded_chunks: list[dict[str, Any]], 
                        output_dir: str = "data/feature_pipeline_data/embedded_data"
                        ) -> None:
    """
    Save embedded chunks to a JSON file.
    
    Args:
        embedded_chunks (list[dict]): List of chunks with embeddings
        original_filename (str): Original chunk filename for naming
        
    Returns:
        str: Path to the output file
    """
    try:
        # Save to file
        file_id = embedded_chunks[0].get('file_id', '')
        output_filename = f"embedded_{file_id}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(embedded_chunks, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(embedded_chunks)} embedded chunks to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving embedded chunks: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    # Set API key in environment variable or pass directly
    # os.environ["OPENAI_API_KEY"] = "your-api-key"

    load_dotenv()
    
    processor = EmbeddingProcessor()
    output_files = processor.process_all_chunk_files()
    
    print(f"Created {len(output_files)} embedding files")