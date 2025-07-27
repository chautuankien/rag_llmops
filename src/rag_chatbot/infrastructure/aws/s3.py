from loguru import logger
import boto3
from pathlib import Path
import zipfile
import tempfile
import os

from src.settings import settings

class S3Client:
    def __init__(self, bucket_name: str, region_name: str) -> None:
        """Initialize S3 client and bucket name.

        Args:
            bucket_name (str): Name of the S3 bucket
            no_sign_request (bool, optional): If True will access S3 un-authenticated for public buckets.
                If False will use the AWS credentials set by the user. Defaults to False.
            region (str, optional): AWS region. Defaults to AWS_DEFAULT_REGION or AWS_REGION env var,
                or 'us-east-1'.
        """
        self.bucket_name = bucket_name
        self.region_name = region_name

        self.s3_client = boto3.client("s3", region_name=self.region_name)
    
    def upload_folder(self, folder_path: str | Path, s3_prefix: str) -> None:
        """Upload a folder to S3.

        Args:
            folder_path (Path): Local path to the folder to upload.
            s3_prefix (str): S3 prefix where the folder will be uploaded.
        """
        # Ensure bucket exists before proceeding
        self._create_bucket_if_doesnt_exist()
        
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"The folder {folder_path} does not exist.")
        
        if not folder_path.is_dir():
            raise NotADirectoryError(f"The path {folder_path} is not a directory.")
    
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Walk through all files in the directory
                for root, _, files in os.walk(folder_path):
                    for filename in files:
                        file_path = Path(root) / filename
                        # Add file to zip with relative path
                        zipf.write(file_path, file_path.relative_to(folder_path))

            # Construct S3 key with prefix
            zip_filename = f"{folder_path.name}.zip"
            s3_key = f"{s3_prefix.rstrip('/')}/{zip_filename}".lstrip("/")

            # Upload zip file
            logger.debug(
                f"Uploading {folder_path} to {self.bucket_name} with key {s3_key}"
            )
            self.s3_client.upload_file(temp_zip.name, self.bucket_name, s3_key)

        # Clean up temporary zip file
        os.unlink(temp_zip.name)

    def _create_bucket_if_doesnt_exist(self) -> None:
        """Check if bucket exists and create it if it doesn't.

        Raises:
            Exception: If bucket creation fails or if user lacks necessary permissions
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except self.s3_client.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self.region_name},
                    )
                except self.s3_client.exceptions.ClientError as create_error:
                    raise Exception(
                        f"Failed to create bucket {self.bucket_name}: {str(create_error)}"
                    )
            elif error_code == "403":
                raise Exception(f"No permission to access bucket {self.bucket_name}")
            else:
                raise

if __name__ == "__main__":
    # Example usage
    s3_client = S3Client(
        bucket_name=settings.AWS_S3_BUCKET_NAME,
        region_name=settings.AWS_REGION_NAME,
    )
    folder_path = Path("data") / "notion"
    s3_prefix = "rag_llmops/notion"

    try:
        s3_client.upload_folder(folder_path=folder_path, s3_prefix=s3_prefix)
        logger.info(f"Successfully uploaded {folder_path} to S3 at {s3_prefix}")
    except Exception as e:
        logger.error(f"Failed to upload folder to S3: {e}")
