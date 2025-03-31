from typing_extensions import Annotated

from zenml import step, get_step_context

from src.rag_chatbot.domain.document import Document
from src.rag_chatbot.infrastructure.mongodb.service import MongoDBService

@step
def fetch_from_mongodb(limit: int) -> Annotated[list[Document], "documents"]:
    with MongoDBService(model=Document) as service:
        documents = service.fetch_documents(limit, query={})
    
    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="documents",
        metadata={"count": len(documents)}
    )

    return documents

if __name__ == "__main__":
    docs = fetch_from_mongodb(limit=5)
    print(docs)