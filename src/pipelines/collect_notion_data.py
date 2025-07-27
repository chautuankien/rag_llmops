from typing_extensions import Annotated
from zenml import get_step_context, pipeline
from pathlib import Path
from loguru import logger

from src.steps.collect_notion_data import (
    extract_notion_documents_metadata,
    extract_notion_documents
)
from src.steps.infrastructure import save_documents_to_disk, upload_to_s3

@pipeline(enable_cache=False)
def collect_notion_data(
    database_ids: list[str], data_dir: Path, to_s3: bool = False
) -> None:
    logger.info("Start pipeline: collect_notion_data")

    notion_data_dir = data_dir / "notion"
    notion_data_dir.mkdir(parents=True, exist_ok=True)

    invocation_ids = []
    for index, database_id in enumerate(database_ids):
        documents_metadata = extract_notion_documents_metadata(database_id=database_id)
        documents_data = extract_notion_documents(documents_metadata=documents_metadata)

        result = save_documents_to_disk(
            documents=documents_data,
            output_dir=notion_data_dir / f"database_{index}",
        )
        invocation_ids.append(result.invocation_id)

    if to_s3:
        upload_to_s3(
            folder_path=str(notion_data_dir),
            s3_prefix="rag_llmops/notion",
            after=invocation_ids,
        )
    
    logger.info("End pipeline: collection_notion_data")

if __name__ == "__main__":  
    collect_notion_data(
        database_ids=["23d6c88a5848811b88d8fb1a5028e5b1"],
        data_dir=Path("data"),
        to_s3=True,
    )