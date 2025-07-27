import os
import json
import hashlib
from typing import Any, Tuple
from typing_extensions import Annotated

from zenml import get_step_context, step

from loguru import logger

@step
def chunk_documents(documents: list[dict[str, Any]],
                    chunk_size: int = 500, 
                    chunk_overlap: int = 50,
                    output_dir="pipeline_outputs/feature_pipeline_output/chunked_data"
                    ) -> Annotated[list[dict[str, Any]], "chunked documents"]:
    """
    Chunk a list of documents.
    
    Args:
        documents (list[dict]): List of document dictionaries with "markdown_content"
        
    Returns:
        list[dict]: List of chunks with metadata
    """
    all_chunks = []
    
    for doc in documents:
        try:
            logger.info(f"Chunking document from: {doc.get('document_url', 'Unknown URL')}")
            
            # Get document content and metadata
            content = doc.get('markdown_content', '')
            url = doc.get('document_url', '')
            file_id = doc.get('file_id', '')
            
            # Create chunks
            doc_chunks = _create_chunks(content, chunk_size, chunk_overlap)
            
            # Add metadata to chunks
            chunks_with_metadata = []
            
            for i, chunk_text in enumerate(doc_chunks):
                # Create unique ID for the chunk
                chunk_id = _generate_chunk_id(url, i, chunk_text)
                
                chunk = {
                    "file_id": file_id,
                    "chunk_id": chunk_id,
                    "document_url": url,
                    "chunk_index": i,
                    "total_chunks": len(doc_chunks),
                    "content": chunk_text
                }
                
                chunks_with_metadata.append(chunk)
            
            # Add to results
            all_chunks.extend(chunks_with_metadata)

            # Save chunks to file
            _save_chunks(all_chunks, output_dir)
            
            logger.info(f"Created {len(doc_chunks)} chunks for document: {url}")
            
        except Exception as e:
            logger.error(f"Error chunking document {doc.get('url', 'Unknown')}: {str(e)}")
    
    return all_chunks

def _create_chunks(text: str,
                   chunk_size: int = 500, 
                   chunk_overlap: int = 50 
                   ) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text (str): Text to split into chunks
        
    Returns:
        list[str]: List of text chunks
    """
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for paragraph in paragraphs:
        # Rough character count as proxy for token count
        paragraph_size = len(paragraph)
        
        # If adding this paragraph exceeds chunk size and we already have content,
        # save the current chunk and start a new one
        if current_size + paragraph_size > chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
            # Implement overlap by keeping some paragraphs from the previous chunk
            overlap_size = 0
            overlap_paragraphs = []
            
            # Add paragraphs from the end until we reach desired overlap
            for p in reversed(current_chunk):
                p_size = len(p)
                if overlap_size + p_size <= chunk_overlap:
                    overlap_paragraphs.insert(0, p)
                    overlap_size += p_size
                else:
                    break
            
            # Start new chunk with overlap paragraphs
            current_chunk = overlap_paragraphs
            current_size = overlap_size
        
        # Add paragraph to current chunk
        current_chunk.append(paragraph)
        current_size += paragraph_size
        
        # If a single paragraph exceeds chunk size, force chunking
        if paragraph_size > chunk_size:
            # Simple character-based chunking as fallback
            char_chunks = [paragraph[i:i + chunk_size] 
                            for i in range(0, len(paragraph), chunk_size - chunk_overlap)]
            
            # Replace the last added paragraph with these sub-chunks
            current_chunk.pop()
            
            # Add all complete chunks
            for i in range(len(char_chunks) - 1):
                current_chunk.append(char_chunks[i])
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [char_chunks[i][-chunk_overlap:]] if chunk_overlap > 0 else []
            
            # Keep the last sub-chunk for the next iteration
            current_chunk.append(char_chunks[-1])
            current_size = len(char_chunks[-1])
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def _generate_chunk_id(url: str, index: int, content: str) -> str:
    """
    Generate a unique ID for a chunk.
    
    Args:
        url (str): Source URL
        index (int): Chunk index
        content (str): Chunk content
        
    Returns:
        str: Unique chunk ID
    """
    # Create a hash from URL, index, and first 100 chars of content
    content_sample = content[:100] if content else ""
    hash_input = f"{url}_{index}_{content_sample}"
    return hashlib.md5(hash_input.encode()).hexdigest()

def _save_chunks(chunks: list[dict[str, Any]],
                 output_dir="pipeline_outputs/feature_pipeline_output/chunked_data"
                 ) -> None:
    """
    Save chunks to a JSON file.
    
    Args:
        chunks (list[dict]): list of chunk dictionaries
        url (str): Source URL for filename
    """
    if not chunks:
        return
    
    try:
        # Save to file
        file_id = chunks[0].get('file_id', '')
        output_filename = f"chunks_{file_id}.json"
        output_filepath = os.path.join(output_dir, output_filename)
        
        # Save to file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(chunks)} chunks to {output_filepath}")
        
    except Exception as e:
        logger.error(f"Error saving chunks for {chunks[0].get('document_url', '')}: {str(e)}")

