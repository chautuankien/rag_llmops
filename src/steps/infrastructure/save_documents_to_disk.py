from zenml import step, get_step_context
from pathlib import Path
from typing_extensions import Annotated
import shutil
from loguru import logger

from src.rag_chatbot.domain.document import NotionDocument

@step
def save_documents_to_disk(
    documents: list[NotionDocument],
    output_dir: Path
) -> Annotated[str, "output_dir"]:
    """Save a list of Notion documents to disk.

    Args:
        documents (list[NotionDocument]): List of Notion documents to save.
        output_dir (Path): Directory where the documents will be saved.
    """
    logger.info(f"Start step: save_documents_to_disk with {len(documents)} documents")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for document in documents:
        document.write(output_dir=output_dir, also_save_as_txt=True)

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="output_dir",
        metadata={
            "count": len(documents),
            "output_dir": str(output_dir),
        },
    )

    logger.info(f"End step: save_documents_to_disk with {len(documents)} documents saved to {output_dir}")

    return str(output_dir)