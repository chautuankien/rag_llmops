import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import find_dotenv, load_dotenv

# load_dotenv(find_dotenv())

from src.logger.logger import logger

DOTENV = os.path.join(os.path.dirname(__file__), ".env")

class Settings(BaseSettings):
    """
    A Pydantic-based settings class for managing application configurations.
    """

    model_config = SettingsConfigDict(
        env_file=DOTENV, env_file_encoding="utf-8"
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

try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise SystemExit(e)