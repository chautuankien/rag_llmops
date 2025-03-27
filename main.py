from src.pipelines.etl_pipeline import etl
from dotenv import load_dotenv
import os

load_dotenv()

connection_string = os.environ.get("MONGODB_URI")
database_name: str = "document_store"
collection_name: str = "embeddings"


urls = [
    "https://maximelabonne.substack.com/p/uncensor-any-llm-with-abliteration-d30148b7d43e",
    "https://maximelabonne.substack.com/p/create-mixtures-of-experts-with-mergekit-11b318c99562"
       ]

etl(
    urls,
    connection_string,
    collection_name,
    database_name,
)