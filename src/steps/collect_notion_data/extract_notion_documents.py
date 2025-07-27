from typing_extensions import Annotated
from zenml import get_step_context, step
from loguru import logger

from src.rag_chatbot.domain.document import NotionDocumentMetadata, NotionDocument
from src.rag_chatbot.infrastructure.notion.page import NotionPageClient

@step
def extract_notion_documents(
    documents_metadata: list[NotionDocumentMetadata]
) -> Annotated[list[NotionDocument], "notion_documents"]:
    """Extract content from multiple Notion documents.

    Args:
        documents_metadata: List of document metadata to extract content from.

    Returns:
        list[Document]: List of documents with their extracted content.
    """
    logger.info(f"Start step: extract_notion_documents for {len(documents_metadata)} documents")

    client = NotionPageClient()
    documents = []
    for document_metadata in documents_metadata:
        documents.append(client.extract_document(document_metadata))
    
    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="notion_documents",
        metadata={
            "len_documents": len(documents),
        },
    )

    logger.info(f"End step: extract_notion_documents for {len(documents)} documents")

    return documents

if __name__ == "__main__":
    from src.steps.collect_notion_data.extract_notion_documents_metadata import extract_notion_documents_metadata

    metadata = extract_notion_documents_metadata("23d6c88a5848811b88d8fb1a5028e5b1")
    documents = extract_notion_documents(documents_metadata=metadata)
    # print(documents[0])