from pathlib import Path
from loguru import logger
from typing_extensions import Annotated
from zenml import get_step_context, step

from src.settings import settings
from src.rag_chatbot.infrastructure.aws.s3 import S3Client

@step
def upload_to_s3(
    folder_path: str,
    s3_prefix: str = "",
) -> Annotated[str, "s3_uploaded_output"]:
    """Upload a folder to S3.

    Args:
        folder_path (str): Local path to the folder to upload.
        s3_prefix (str): S3 prefix where the folder will be uploaded.
    """
    logger.info(f"Start step: upload_to_s3 for folder_path: {folder_path} with s3_prefix: {s3_prefix}")
    s3_client = S3Client(
        bucket_name=settings.AWS_S3_BUCKET_NAME,
        region_name=settings.AWS_REGION_NAME,
    )
    
    s3_client.upload_folder(folder_path=folder_path, s3_prefix=s3_prefix)

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="s3_uploaded_output",
        metadata={
            "folder_path": folder_path,
            "s3_prefix": s3_prefix,
        },
    )

    logger.info(f"End step: upload_to_s3 for folder_path: {folder_path} with s3_prefix: {s3_prefix}")

    return str(folder_path)