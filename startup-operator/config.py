"""Configuration loading for AI Startup Operator."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    openai_api_key: str
    openai_model: str
    notion_api_key: str
    notion_parent_page_id: str


def load_settings() -> Settings:
    """Load and validate required settings from environment variables."""
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    notion_api_key = os.getenv("NOTION_API_KEY", "").strip()
    notion_parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()

    missing = []
    if not openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not notion_api_key:
        missing.append("NOTION_API_KEY")
    if not notion_parent_page_id:
        missing.append("NOTION_PARENT_PAGE_ID")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {joined}")

    return Settings(
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        notion_api_key=notion_api_key,
        notion_parent_page_id=notion_parent_page_id,
    )
