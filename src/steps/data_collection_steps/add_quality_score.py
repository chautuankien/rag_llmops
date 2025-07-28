from loguru import logger
from typing_extensions import Annotated
from zenml import step, get_step_context

from src.rag_chatbot.agents.quality import QualityScoreAgent
from src.rag_chatbot.domain.document import Document, ArticleDocument, NotionDocument

# Define the same union type
DocumentTypes = ArticleDocument | NotionDocument

@step(enable_cache=True)
def add_quality_score(
    documents: list[DocumentTypes],
    model_id = "gpt-4o-mini",
    mock: bool = True,
    max_concurrent_requests: int = 5
) -> Annotated[list[Document], "scored_documents"]:
    """Add quality scores to a list of documents."""
    logger.info("----Start adding quality scores----")

    # Initialize the quality agent
    quality_agent = QualityScoreAgent(model_id=model_id, mock=mock, max_concurrent_requests=max_concurrent_requests)

    scored_documents = quality_agent(documents)

    len_documents = len(documents)
    len_documents_with_scores = len(
        [doc for doc in scored_documents if doc.content_quality_score is not None]
    )
    logger.info(f"Total documents: {len_documents}")
    logger.info(f"Total documents that were scored: {len_documents_with_scores}")

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="scored_documents",
        metadata={
            "len_documents": len_documents,
            "len_documents_with_scores": len_documents_with_scores,
        },
    )

    logger.info("----End adding quality scores----")
    
    return scored_documents