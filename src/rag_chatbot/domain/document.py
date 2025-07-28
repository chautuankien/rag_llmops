from abc import ABC, abstractmethod
from typing import Dict, Any
import uuid
from pydantic import BaseModel, Field
from pathlib import Path
import json

## Base Document Class
# Represents a generic document with basic attributes
class Document(BaseModel, ABC):
    id: str | None = None
    content: str | None = None
    content_quality_score: float | dict | None = None
    summary: str | None = None

    def add_quality_score(self, score: float) -> "Document":
        """Add a quality score to the document."""
        self.content_quality_score = score
        return self


## Article Document Class
# Represents a document extracted from an article
class ArticleDocument(Document):
    url: str | None = None
    title: str | None = None
    language: str | None = None
    author: str | None = None
    platform: str | None = None


## Notion Document Classes
# Represents metadata about a Notion document
class NotionDocumentMetadata(BaseModel):
    id: str
    url: str
    title: str
    properties: dict

# Represents a Notion document with its content and metadata
class NotionDocument(Document):
    metadata: NotionDocumentMetadata
    parent_metadata: NotionDocumentMetadata | None = None
    child_urls: list[str] = Field(default_factory=list)

    def write(
        self, output_dir: Path, also_save_as_txt: bool = False
    ) -> None:
        """Write document data to file, optionally obfuscating sensitive information.

        Args:
            output_dir: Directory path where the files should be written.
            obfuscate: If True, sensitive information will be obfuscated.
            also_save_as_txt: If True, content will also be saved as a text file.
        """

        output_dir.mkdir(parents=True, exist_ok=True)

        json_page = self.model_dump()

        output_file = output_dir / f"{self.id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                json_page,
                f,
                indent=4,
                ensure_ascii=False,
            )

        if also_save_as_txt:
            txt_path = output_file.with_suffix(".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(self.content)