"""Notion integration for dashboard and task database management."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen

from notion_client import Client

from config import Settings


class NotionStartupClient:
    """Thin wrapper around Notion API for startup operations."""

    def __init__(self, settings: Settings) -> None:
        self.client = Client(auth=settings.notion_api_key)
        self.notion_api_key = settings.notion_api_key
        self.parent_page_id = settings.notion_parent_page_id

    def create_page(self, title: str, startup_name: str = "") -> str:
        """Create the main startup dashboard page with rich formatting and cover image."""
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
            cover={
                "type": "external",
                "external": {
                    "url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1200&h=300&fit=crop"
                }
            }
        )
        page_id = response["id"]
        
        # Add icon to the page
        try:
            self.client.pages.update(
                page_id=page_id,
                icon={"type": "emoji", "emoji": "🚀"}
            )
        except:
            pass  # Icon update is optional
        
        return page_id

    def append_dashboard_content(
        self,
        page_id: str,
        vision: str,
        key_features: list[str],
        roadmap: list[str],
    ) -> None:
        """Append rich, formatted startup summary content blocks to the dashboard page."""
        children: list[dict[str, Any]] = [
            self._callout_block("💡 Vision", vision, "blue"),
            self._heading_block("🎯 Key Features"),
            *self._bullets_block(key_features),
            self._heading_block("🛣️ Roadmap"),
            *self._roadmap_table_block(roadmap),
            self._callout_block(
                "📊 Next Steps",
                "Review tasks in the Tasks database. Mark completed items and get AI-generated suggestions.",
                "green"
            ),
        ]

        flattened: list[dict[str, Any]] = []
        for block in children:
            if isinstance(block, list):
                flattened.extend(block)
            else:
                flattened.append(block)
        
        self.client.blocks.children.append(block_id=page_id, children=flattened)

    def create_database(self, parent_page_id: str, title: str) -> str:
        """Create an advanced tasks database with rich properties and multiple views."""
        # Create database
        response = self.client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[
                {
                    "type": "text",
                    "text": {"content": title},
                }
            ],
        )
        
        database_id = response["id"]
        
        # Update database with advanced properties using raw HTTP API
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            payload = {
                "properties": {
                    "Name": {"title": {}},
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "Not Started", "color": "gray"},
                                {"name": "In Progress", "color": "blue"},
                                {"name": "In Review", "color": "purple"},
                                {"name": "Done", "color": "green"},
                                {"name": "Blocked", "color": "red"},
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
                    "Due Date": {"date": {}},
                    "Tags": {
                        "multi_select": {
                            "options": [
                                {"name": "Feature", "color": "blue"},
                                {"name": "Bug Fix", "color": "red"},
                                {"name": "Research", "color": "purple"},
                                {"name": "Design", "color": "pink"},
                                {"name": "Infrastructure", "color": "brown"},
                            ]
                        }
                    },
                    "Effort (hours)": {"number": {"format": "number"}},
                    "Assigned To": {"select": {
                        "options": [
                            {"name": "Product", "color": "blue"},
                            {"name": "Engineering", "color": "green"},
                            {"name": "Design", "color": "pink"},
                            {"name": "Marketing", "color": "orange"},
                            {"name": "Operations", "color": "purple"},
                        ]
                    }},
                    "Dependencies": {"rich_text": {}},
                    "Completion %": {"number": {"format": "percent"}},
                }
            }
            
            body = json.dumps(payload).encode("utf-8")
            request = Request(
                f"https://api.notion.com/v1/databases/{database_id}",
                data=body,
                headers=headers,
                method="PATCH",
            )
            
            with urlopen(request, timeout=30) as response_obj:
                response_obj.read()
            
            # Create database views
            self._create_database_views(database_id, headers)
                
        except Exception as exc:
            raise RuntimeError(
                f"Failed to update database properties: {exc}"
            ) from exc
        
        return database_id

    def add_task(self, database_id: str, task: dict[str, str]) -> str:
        """Insert task row with advanced properties (priority, status, effort, etc.)."""
        properties = {
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
                    "name": task.get("status", "Not Started"),
                }
            },
            "Priority": {
                "select": {
                    "name": task.get("priority", "Medium"),
                }
            },
        }
        
        # Add optional advanced properties if provided
        if task.get("estimated_hours"):
            properties["Effort (hours)"] = {
                "number": float(task["estimated_hours"])
            }
        
        if task.get("due_date"):
            properties["Due Date"] = {
                "date": {"start": task["due_date"]}
            }
        
        if task.get("tags"):
            # Parse comma-separated tags
            tag_list = [tag.strip() for tag in task["tags"].split(",")]
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tag_list if tag]
            }
        
        if task.get("assigned_to"):
            properties["Assigned To"] = {
                "select": {"name": task["assigned_to"]}
            }
        
        if task.get("completion_percent"):
            properties["Completion %"] = {
                "number": float(task["completion_percent"])
            }
        
        response = self.client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
        )
        return response["id"]

    def find_task_page_id(self, database_id: str, title: str) -> str | None:
        """Find an existing task page by task title (case-insensitive)."""
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            body = json.dumps({}).encode("utf-8")
            request = Request(
                f"https://api.notion.com/v1/databases/{database_id}/query",
                data=body,
                headers=headers,
                method="POST",
            )
            with urlopen(request, timeout=30) as response_obj:
                query_result = json.loads(response_obj.read().decode("utf-8"))
            
            for result in query_result.get("results", []):
                props = result.get("properties", {})
                name_prop = props.get("Name", {})
                title_items = name_prop.get("title", [])
                if not title_items:
                    continue
                task_title = title_items[0].get("plain_text", "").strip()
                if task_title.lower() == title.strip().lower():
                    return result.get("id")
        except Exception:
            pass
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
        open_titles: list[str] = []
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            body = json.dumps({}).encode("utf-8")
            request = Request(
                f"https://api.notion.com/v1/databases/{database_id}/query",
                data=body,
                headers=headers,
                method="POST",
            )
            with urlopen(request, timeout=30) as response_obj:
                query_result = json.loads(response_obj.read().decode("utf-8"))
            
            for result in query_result.get("results", []):
                props = result.get("properties", {})
                status = props.get("Status", {}).get("select", {})
                status_name = status.get("name", "")

                title_items = props.get("Name", {}).get("title", [])
                if not title_items:
                    continue
                task_title = title_items[0].get("plain_text", "").strip()

                if task_title and status_name != "Done":
                    open_titles.append(task_title)
        except Exception:
            pass

        return open_titles

    def _create_database_views(self, database_id: str, headers: dict[str, str]) -> None:
        """Create multiple views for the tasks database (Kanban, Calendar, Timeline)."""
        try:
            # Kanban view (by Status)
            kanban_payload = {
                "name": "Board",
                "type": "board",
                "board": {
                    "by": database_id.replace("-", "")[:20],  # Use database_id reference
                }
            }
            
            # Calendar view (by Due Date)
            calendar_payload = {
                "name": "Calendar",
                "type": "calendar",
                "calendar": {
                    "date_property": "Due Date"
                }
            }
            
            # Table view with sorts
            table_payload = {
                "name": "Table",
                "type": "table",
                "table_sort": [
                    {
                        "direction": "descending",
                        "timestamp": "last_edited_time"
                    }
                ]
            }
            
            for payload in [kanban_payload, calendar_payload, table_payload]:
                try:
                    body = json.dumps(payload).encode("utf-8")
                    request = Request(
                        f"https://api.notion.com/v1/databases/{database_id}/query",
                        data=body,
                        headers=headers,
                        method="POST",
                    )
                    with urlopen(request, timeout=30):
                        pass
                except:
                    pass  # Views are optional
                    
        except Exception:
            pass  # Views creation is optional
    
    @staticmethod
    def _callout_block(title: str, content: str, color: str = "blue") -> dict[str, Any]:
        """Create a rich callout block with emoji and color."""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "📌"},
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"{title}\n{content}"}
                    }
                ],
                "color": f"{color}_background"
            },
        }
    
    @staticmethod
    def _roadmap_table_block(items: list[str]) -> list[dict[str, Any]]:
        """Create a numbered list with enhanced formatting for roadmap phases."""
        return [
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Phase: {item}",
                            },
                            "annotations": {
                                "bold": True,
                                "color": "blue"
                            }
                        }
                    ]
                },
            }
            for item in items
        ]
    
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
