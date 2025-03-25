from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
from pydantic import BaseModel, UUID4

class Document(BaseModel):
    content: dict
    platform: str

class ArticleDocument(Document):
    url: str