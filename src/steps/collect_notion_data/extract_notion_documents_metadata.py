from typing_extensions import Annotated
from zenml import get_step_context, step
from loguru import logger

from src.rag_chatbot.infrastructure.notion.notion_client import NotionClient
from src.rag_chatbot.domain.document import NotionDocumentMetadata

@step
def extract_notion_documents_metadata(
    database_id: str
) -> Annotated[list[NotionDocumentMetadata], "notion_documents_metadata"]:
    """Extract metadata from Notion documents in a specified database.

    Args:
        database_id: The ID of the Notion database to query.

    Returns:
        A list of NotionDocumentMetadata objects containing the extracted information.
    """
    logger.info(f"Start step: extract_notion_documents_metadata for database_id: {database_id}")

    client = NotionClient()
    documents_metadata = client.query_notion_database(database_id)

    logger.info(
        f"Extracted {len(documents_metadata)} documents metadata from {database_id}"
    )

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="notion_documents_metadata",
        metadata={
            "database_id": database_id,
            "len_documents_metadata": len(documents_metadata),
        },
    )
    logger.info(f"End step: extract_notion_documents_metadata for database_id: {database_id}")

    return documents_metadata

if __name__ == "__main__":
    metadata = extract_notion_documents_metadata("23d6c88a5848811b88d8fb1a5028e5b1")
    print(metadata[0])
