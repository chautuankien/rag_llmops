import requests
from typing import Any
from loguru import logger

from src.settings import settings
from src.rag_chatbot.domain.document import NotionDocumentMetadata

class NotionClient:
    def __init__(self, api_key: str | None = settings.NOTION_SECRET_KEY) -> None:
        assert api_key is not None, (
            "NOTION_SECRET_KEY environment variable is required. Set it in your .env file."
        )

        self.api_key = api_key

    def query_notion_database(self, database_id: str):
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        try:
            response = requests.post(
                url, headers=headers, timeout=10
            )
            response.raise_for_status()
            results = response.json()
            results = results["results"]
        except requests.exceptions.RequestException:
            logger.opt(exception=True).debug("Error querying Notion database")
            return []
        except KeyError:
            logger.opt(exception=True).debug(
                "Unexpected response format from Notion API"
            )
            return []
        except Exception:  # noqa: BLE001
            logger.opt(exception=True).debug("Error querying Notion database")
            return []
        
        return [self.__build_page_metadata(page) for page in results]
    
    def query_notion_page(self, page_id: str):
        url: str = f"https://api.notion.com/v1/pages/{page_id}"
        header = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        try:
            response = requests.get(
                url, headers=header, timeout=10
            )
            response.raise_for_status()
            results = response.json()
            results = results["results"]
        except requests.exceptions.RequestException:
            logger.opt(exception=True).debug("Error querying Notion database")
            return []
        except KeyError:
            logger.opt(exception=True).debug(
                "Unexpected response format from Notion API"
            )
            return []
        except Exception:  # noqa: BLE001
            logger.opt(exception=True).debug("Error querying Notion database")
            return []

        return results

    def __build_page_metadata(self, page: dict[str, Any]) -> NotionDocumentMetadata:
        """Build a PageMetadata object from a Notion page dictionary.

        Args:
            page: Dictionary containing Notion page data.

        Returns:
            A PageMetadata object containing the processed page data.
        """
        properties = self.__flatten_properties(page.get("properties", {}))
        title = properties.pop("Title")

        if page.get("parent"):
            properties["parent"] = {
                "id": page["parent"]["database_id"],
                "url": "",
                "title": "",
                "properties": {},
            }

        return NotionDocumentMetadata(
            id=page["id"], url=page["url"], title=title, properties=properties
        )
    
    def __flatten_properties(self, properties: dict) -> dict:
        """Flatten Notion properties dictionary into a simpler key-value format.

        Args:
            properties: Dictionary of Notion properties to flatten.

        Returns:
            A flattened dictionary with simplified key-value pairs.

        Example:
            Input: {
                'Type': {'type': 'select', 'select': {'name': 'Leaf'}},
                'Name': {'type': 'title', 'title': [{'plain_text': 'Merging'}]}
            }
            Output: {
                'Type': 'Leaf',
                'Name': 'Merging'
            }
        """
        flattened = {}

        for key, value in properties.items():
            prop_type = value.get("type")

            if prop_type == "select":
                select_value = value.get("select", {}) or {}
                flattened[key] = select_value.get("name")
            elif prop_type == "multi_select":
                flattened[key] = [
                    item.get("name") for item in value.get("multi_select", [])
                ]
            elif prop_type == "title":
                flattened[key] = "\n".join(
                    item.get("plain_text", "") for item in value.get("title", [])
                )
            elif prop_type == "rich_text":
                flattened[key] = " ".join(
                    item.get("plain_text", "") for item in value.get("rich_text", [])
                )
            elif prop_type == "number":
                flattened[key] = value.get("number")
            elif prop_type == "checkbox":
                flattened[key] = value.get("checkbox")
            elif prop_type == "date":
                date_value = value.get("date", {})
                if date_value:
                    flattened[key] = {
                        "start": date_value.get("start"),
                        "end": date_value.get("end"),
                    }
            elif prop_type == "database_id":
                flattened[key] = value.get("database_id")
            elif prop_type == "url":
                flattened[key] = value.get("url")
            else:
                flattened[key] = value

        return flattened
    
if __name__ == "__main__":
    client = NotionClient()
    results = client.query_notion_database("5a1efe6286a74a59a370991eecb159fc")
    for page in results:
        print(page)
        break
    # results = client.query_notion_page("17c6c88a5848800e8971dc052638e8a5")
    # print(results)