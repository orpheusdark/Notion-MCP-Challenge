"""Configuration loading for AI Startup Operator."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    groq_api_key: str
    groq_model: str
    notion_api_key: str
    notion_parent_page_id: str


def load_settings() -> Settings:
    """Load and validate required settings from environment variables."""
    load_dotenv()

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    notion_api_key = os.getenv("NOTION_API_KEY", "").strip()
    notion_parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()

    missing = []
    if not groq_api_key:
        missing.append("GROQ_API_KEY")
    if not notion_api_key:
        missing.append("NOTION_API_KEY")
    if not notion_parent_page_id:
        missing.append("NOTION_PARENT_PAGE_ID")

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {joined}")

    return Settings(
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        notion_api_key=notion_api_key,
        notion_parent_page_id=notion_parent_page_id,
    )
