"""Notion integration for dashboard and task database management."""

from __future__ import annotations

from typing import Any

from notion_client import Client

from config import Settings


class NotionStartupClient:
    """Thin wrapper around Notion API for startup operations."""

    def __init__(self, settings: Settings) -> None:
        self.client = Client(auth=settings.notion_api_key)
        self.parent_page_id = settings.notion_parent_page_id

    def create_page(self, title: str) -> str:
        """Create the main startup dashboard page and return its ID."""
        response = self.client.pages.create(
            parent={"type": "page_id", "page_id": self.parent_page_id},
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title},
                        }
                    ]
                }
            },
        )
        return response["id"]

    def append_dashboard_content(
        self,
        page_id: str,
        vision: str,
        key_features: list[str],
        roadmap: list[str],
    ) -> None:
        """Append startup summary content blocks to the dashboard page."""
        children: list[dict[str, Any]] = [
            self._heading_block("Vision"),
            self._paragraph_block(vision),
            self._heading_block("Key Features"),
            self._bullets_block(key_features),
            self._heading_block("Roadmap"),
            self._numbered_block(roadmap),
        ]

        flattened: list[dict[str, Any]] = []
        for block in children:
            if isinstance(block, list):
                flattened.extend(block)
            else:
                flattened.append(block)

        self.client.blocks.children.append(block_id=page_id, children=flattened)

    def create_database(self, parent_page_id: str, title: str) -> str:
        """Create a tasks database under the dashboard page and return database ID."""
        response = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[
                {
                    "type": "text",
                    "text": {"content": title},
                }
            ],
            properties={
                "Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Not Started", "color": "gray"},
                            {"name": "In Progress", "color": "yellow"},
                            {"name": "Done", "color": "green"},
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "blue"},
                            {"name": "Medium", "color": "orange"},
                            {"name": "High", "color": "red"},
                        ]
                    }
                },
            },
        )
        return response["id"]

    def add_task(self, database_id: str, task: dict[str, str]) -> str:
        """Insert one task row into the Notion task database."""
        response = self.client.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": task["title"],
                            }
                        }
                    ]
                },
                "Status": {
                    "select": {
                        "name": task["status"],
                    }
                },
                "Priority": {
                    "select": {
                        "name": task["priority"],
                    }
                },
            },
        )
        return response["id"]

    def find_task_page_id(self, database_id: str, title: str) -> str | None:
        """Find an existing task page by task title (case-insensitive)."""
        query = self.client.databases.query(database_id=database_id)
        for result in query.get("results", []):
            props = result.get("properties", {})
            name_prop = props.get("Name", {})
            title_items = name_prop.get("title", [])
            if not title_items:
                continue
            task_title = title_items[0].get("plain_text", "").strip()
            if task_title.lower() == title.strip().lower():
                return result.get("id")
        return None

    def update_task_status(self, task_page_id: str, status: str) -> None:
        """Update a task's status field."""
        self.client.pages.update(
            page_id=task_page_id,
            properties={
                "Status": {
                    "select": {
                        "name": status,
                    }
                }
            },
        )

    def get_open_task_titles(self, database_id: str) -> list[str]:
        """Return all task titles not marked Done."""
        query = self.client.databases.query(database_id=database_id)
        open_titles: list[str] = []
        for result in query.get("results", []):
            props = result.get("properties", {})
            status = props.get("Status", {}).get("select", {})
            status_name = status.get("name", "")

            title_items = props.get("Name", {}).get("title", [])
            if not title_items:
                continue
            task_title = title_items[0].get("plain_text", "").strip()

            if task_title and status_name != "Done":
                open_titles.append(task_title)

        return open_titles

    @staticmethod
    def _heading_block(text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    @staticmethod
    def _paragraph_block(text: str) -> dict[str, Any]:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            },
        }

    @staticmethod
    def _bullets_block(items: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": item,
                            },
                        }
                    ]
                },
            }
            for item in items
        ]

    @staticmethod
    def _numbered_block(items: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": item,
                            },
                        }
                    ]
                },
            }
            for item in items
        ]
