import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import find_dotenv, load_dotenv

# load_dotenv(find_dotenv())

from loguru import logger

DOTENV = os.path.join(os.getcwd(), ".env")
# print(DOTENV)

class Settings(BaseSettings):
    """
    A Pydantic-based settings class for managing application configurations.
    """

    model_config = SettingsConfigDict(
        env_file=DOTENV, env_file_encoding="utf-8", extra='ignore'
    )

    # OPENAI API
    OPENAI_MODEL_ID: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model"
    )
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="API key for OpenAI service authentication.",
    )

    # MongoDB database
    MONGODB_URI: str = Field(
        default="mongodb+srv://llmragchatbot:llmragchatbot@llmragchatbot.zipta.mongodb.net/",
        description="Connection URI for the local MongoDB Atlas instance.",
    )
    MONGODB_DATABASE_NAME: str = Field(
        default="llm_rag_db",
        description="Name of the MongoDB database.",
    )
    MONGODB_COLLECTION_NAME: str = Field(
        default="source_urls",
        description="Name of the MongoDB database.",
    )

    # Notion API Configuration
    NOTION_SECRET_KEY: str = Field(
        default=None,
        description="Secret key for Notion API authentication"
    )

    # AWS S3 Configuration
    AWS_REGION_NAME: str = Field(
        default="ap-northeast-1",
        description="AWS region for S3 bucket operations"
    )
    AWS_S3_BUCKET_NAME: str = Field(
        default="rag-llmops-bucket",
        description="Name of the S3 bucket for storing data"
    )

try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise SystemExit(e)