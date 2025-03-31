from src.steps.feature_steps.fetch_from_mongodb import fetch_from_mongodb
from dotenv import load_dotenv
import os

load_dotenv()



docs = fetch_from_mongodb(limit=5)
print(docs)