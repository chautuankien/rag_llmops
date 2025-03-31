import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import os
import json
from typing import Any
from typing_extensions import Annotated

from zenml import get_step_context, step

from src.logger.logger import logger
from src.rag_chatbot.domain.document import Document

@step
def data_extraction(
    documents: list[Document], 
    delay: int=1,
    output_dir: str ="pipeline_outputs/feature_pipeline_output/crawled_data",
    ) -> Annotated[list[dict[str, Any]], "extracted documents"]:
    """
    Extract content from a list of URLs and convert to markdown.
    
    Args:
        urls (list): List of URLs to crawl
        delay (int): Delay between requests in seconds
        logger: Optional logger instance. If None, will get one from LoggerSingleton
        
    Returns:
        list: List of dictionaries containing URL and markdown content
    """
    results = []
    file_id = int(time.time())
    
    for doc in documents:
        try:
            logger.info(f"Processing URL: {doc}")
            
            # Extract content
            content = _fetch_url(doc)
            
            if content:
                # Convert to markdown
                md_content = _html_to_markdown(content)
                
                # Add to results
                results.append({
                    "file_id": file_id,
                    "document_url": url,
                    "markdown_content": md_content,
                })

                logger.info(f"Successfully processed and saved: {url}")
            
            else:
                logger.warning(f"No content extracted from: {url}")
            
            # Save extracted data to file
            _save_extracted_data(results, output_dir)

            step_context = get_step_context()
            step_context.add_output_metadata(
                output_name="extracted documents",
                metadata={
                    "len_urls": len(urls),
                    }
                )
            
            # Respect robots.txt with delay
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
    
    return results

def _fetch_url(url: str) -> str | None:
    """
    Fetch URL content.
    
    Args:
        url (str): URL to fetch
        
    Returns:
        str: HTML content or None if failed
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return None

def _html_to_markdown(html_content: str) -> str:
    """
    Convert HTML to standardized markdown.
    
    Args:
        html_content (str): HTML content to convert
        
    Returns:
        str: Markdown content
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Extract title
        title = soup.title.string if soup.title else "No Title"
        
        # Extract main content - focus on article or main content
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        
        # Format as markdown
        md_content = f"# {title}\n\n{text}"
        
        return md_content
    
    except Exception as e:
        logger.error(f"Error converting HTML to markdown: {str(e)}")
        return "Error converting content to markdown"

def _save_extracted_data(extracted_data: list[dict[str, Any]],
                         output_dir: str = "pipeline_outputs/feature_pipeline_output/crawled_data",
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
        file_id = extracted_data[0].get('file_id', '')
        output_filename = f"extracted_{file_id}.json"
        output_filepath = os.path.join(output_dir, output_filename)
        
        # Save to file
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved {len(extracted_data)} data to {output_filepath}")

    except Exception as e:
        logger.error(f"Error saving extracted data for {extracted_data[0].get('document_url', )}: {str(e)}")
        
# Example usage
if __name__ == "__main__":
    sample_urls = [
        "https://docs.zenml.io/getting-started/installation",
    ]
    
    results = extract_from_urls(sample_urls)
    print(f"Processed {len(results)} URLs successfully")