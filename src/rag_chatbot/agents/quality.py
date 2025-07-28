import os
import asyncio
import json
import psutil
import tiktoken
from loguru import logger
from tqdm import tqdm
from litellm import acompletion
from pydantic import BaseModel

from src.rag_chatbot.domain.document import Document

class QualityScoreResponseFormat(BaseModel):
    """Format for quality score responses from the language model.

    Attributes:
        score: A float between 0.0 and 1.0 representing the quality score.
    """

    score: float

class QualityScoreAgent:
    """Evaluates the quality of documents using LiteLLM with async support.

    This class handles the interaction with language models through LiteLLM to
    evaluate document quality based on relevance, factual accuracy, and information
    coherence. It supports both single and batch document processing.

    Attributes:
        model_id: The ID of the language model to use for quality evaluation.
        mock: If True, returns mock quality scores instead of using the model.
        max_concurrent_requests: Maximum number of concurrent API requests.
    """

    SYSTEM_PROMPT_TEMPLATE = """You are an expert judge tasked with evaluating the quality of a given DOCUMENT.

Guidelines:
1. Evaluate the DOCUMENT based on generally accepted facts and reliable information.
2. Evaluate that the DOCUMENT contains relevant information and not only links or error messages.
3. Check that the DOCUMENT doesn't oversimplify or generalize information in a way that changes its meaning or accuracy.

Analyze the text thoroughly and assign a quality score between 0 and 1, where:
- **0.0**: The DOCUMENT is completely irrelevant containing only noise such as links or error messages
- **0.1 - 0.7**: The DOCUMENT is partially relevant containing some relevant information checking partially guidelines
- **0.8 - 1.0**: The DOCUMENT is entirely relevant containing all relevant information following the guidelines

It is crucial that you return only the score in the following JSON format:
{{
    "score": <your score between 0.0 and 1.0>
}}

DOCUMENT:
{document}
"""

    def __init__(self, model_id: str, mock: bool = False, max_concurrent_requests: int = 5):
        """Initialize the QualityScoreAgent.

        Args:
            model_id: The ID of the language model to use for quality evaluation.
            mock: If True, returns mock quality scores instead of using the model.
            max_concurrent_requests: Maximum number of concurrent API requests.
        """
        self.model_id = model_id
        self.mock = mock
        self.max_concurrent_requests = max_concurrent_requests
    
    def __call__(self, documents: Document | list[Document]) -> Document | list[Document]:
        """Process single document or batch of documents for summarization.

        Args:
            documents: Single Document or list of Documents to summarize.

        Returns:
            Document | list[Document]: Processed document(s) with summaries.
        """

        is_single_document = isinstance(documents, Document)
        docs_list = [documents] if is_single_document else documents

        # Try to get the current running asyncio event loop (works if already inside an async context)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # If there is no running event loop (i.e., not in an async context), run the coroutine using asyncio.run()
            results = asyncio.run(self._get_quality_score_batch(docs_list))
        else:
            # If a running event loop exists, schedule the coroutine to run until complete using that loop
            results = loop.run_until_complete(self._get_quality_score_batch(docs_list))
    
        return results[0] if is_single_document else results
    
    async def _get_quality_score_batch(self, documents: list[Document]) -> list[Document]:
        """Asynchronously get quality scores for a batch of documents.

        Args:
            documents: List of Document objects to evaluate.

        Returns:
            List of Document objects with updated quality scores.
        """
        process = psutil.Process(os.getpid())
        # get the current RAM usage of the process in bytes
        start_mem = process.memory_info().rss
        total_docs = len(documents)
        logger.debug(
            f"Starting quality scoring batch with {self.max_concurrent_requests} concurrent requests. "
            f"Current process memory usage: {start_mem // (1024 * 1024)} MB"
        )

        scored_documents = await self._process_batch(documents, await_time_seconds=7)

        end_mem = process.memory_info().rss
        memory_diff = end_mem - start_mem
        logger.debug(
            f"Quality scoring batch completed. "
            f"Final process memory usage: {end_mem // (1024 * 1024)} MB, "
            f"Memory diff: {memory_diff // (1024 * 1024)} MB"
        )

        success_count = len(
            [doc for doc in scored_documents if hasattr(doc, "quality_score")]
        )
        failed_count = total_docs - success_count
        logger.info(
            f"Quality scoring completed: "
            f"{success_count}/{total_docs} succeeded ✓ | "
            f"{failed_count}/{total_docs} failed ✗"
        )

        return scored_documents
    
    async def _process_batch(self, documents: list[Document], await_time_seconds: int = 7) -> list[Document]:
        """Process a batch of documents asynchronously with rate limiting.

        Args:
            documents: List of Document objects to process.
            await_time_seconds: Time to wait between processing batches.

        Returns:
            List of Document objects with updated quality scores.
        """
        # Create a semaphore to limit the number of concurrent tasks can access the resource
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        tasks = [
            self._get_quality_score(
                document, semaphore, await_time_seconds=await_time_seconds
            )
            for document in documents
        ]

        results = []
        for coro in tqdm(
            asyncio.as_completed(tasks),
            total=len(documents),
            desc="Processing documents",
            unit="doc",
        ):
            result = await coro
            results.append(result)

        return results

    async def _get_quality_score(
        self, document: Document, semaphore: asyncio.Semaphore, await_time_seconds: int = 7
    ) -> Document:
        """Get the quality score for a single document asynchronously.

        Args:
            document: Document object to evaluate.
            semaphore: Semaphore to limit concurrent access.
            await_time_seconds: Time to wait before timing out.

        Returns:
            Document object with updated quality score.
        """
        if self.mock:
            return document.add_quality_score(score=0.5)

        async def process_document() -> Document:
            """Process the document to get its quality score."""
            input_user_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(document=document.content)
            try:
                input_user_prompt = clip_tokens(
                    input_user_prompt, max_tokens=8192, model_id=self.model_id
                )
            except Exception as e:
                logger.warning(
                    f"Failed to clip tokens for document {document.id}: {str(e)}"
                )
            
            try:
                response = await acompletion(
                    model=self.model_id,
                    messages=[
                        {"role": "user", "content": input_user_prompt}
                    ],
                    stream=False
                )
                await asyncio.sleep(await_time_seconds)  # Simulate processing time

                if not response.choices:
                    logger.warning(f"No quality score returned for document {document.id}")

                    return document
                
                response_content = response.choices[0].message.content
                quality_score = self._parse_model_output(response_content)
                if not quality_score:
                    logger.warning(f"Failed to parse model output for document {document.id}")
                    return document
                return document.add_quality_score(score=quality_score)
            except Exception as e:
                logger.error(
                    f"Error processing document {document.id} for quality score: {str(e)}"
                )
                return document
        
        if semaphore:
            async with semaphore:
                return await process_document()

        return await process_document()
    
    def _parse_model_output(self, answer: str | None) -> QualityScoreResponseFormat | None:
        if not answer:
            return None

        try:
            dict_content = json.loads(answer)
            return QualityScoreResponseFormat(
                score=dict_content["score"],
            )
        except Exception:
            return None


def clip_tokens(text: str, max_tokens: int, model_id: str) -> str:
    """Clip the text to a maximum number of tokens using the tiktoken tokenizer.

    Args:
        text: The input text to clip.
        max_tokens: Maximum number of tokens to keep (default: 8192).
        model_id: The model name to determine encoding (default: "gpt-4").

    Returns:
        str: The clipped text that fits within the token limit.
    """

    try:
        encoding = tiktoken.encoding_for_model(model_id)
    except KeyError:
        # Fallback to cl100k_base encoding (used by gpt-4, gpt-3.5-turbo, text-embedding-ada-002)
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text

    return encoding.decode(tokens[:max_tokens])