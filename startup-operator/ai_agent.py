"""OpenAI-powered planning agent for startup operations."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from config import Settings
from utils import parse_json_strict, validate_initial_plan, validate_iteration_plan


class AIAgent:
    """Encapsulates all LLM interactions with strict JSON contracts."""

    def __init__(self, settings: Settings) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def generate_initial_plan(self, idea: str) -> dict[str, Any]:
        """Generate startup dashboard content and initial task list."""
        system_prompt = (
            "You are an expert startup operator. "
            "Return only valid JSON with no markdown, no prose, and no code fences. "
            "The JSON schema must be exactly:\n"
            "{\n"
            '  "startup_name": "string",\n'
            '  "vision": "string",\n'
            '  "key_features": ["string"],\n'
            '  "roadmap": ["string"],\n'
            '  "tasks": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "priority": "Low|Medium|High",\n'
            '      "status": "Not Started|In Progress|Done"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Generate 5 to 8 practical tasks and 3 to 5 roadmap phases."
        )

        user_prompt = f"Startup idea: {idea.strip()}"

        raw = self._chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
        return validate_initial_plan(parse_json_strict(raw))

    def generate_next_iteration(
        self,
        startup_name: str,
        startup_vision: str,
        completed_tasks: list[str],
        current_open_tasks: list[str],
    ) -> dict[str, Any]:
        """Generate recommendations and next tasks after progress update."""
        system_prompt = (
            "You are an expert startup operator. "
            "Return only valid JSON with no markdown, no prose, and no code fences. "
            "The JSON schema must be exactly:\n"
            "{\n"
            '  "suggestions": ["string"],\n'
            '  "next_tasks": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "priority": "Low|Medium|High",\n'
            '      "status": "Not Started|In Progress|Done"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Generate 3 concise suggestions and 3 to 5 new tasks that do not duplicate open tasks."
        )

        user_payload = {
            "startup_name": startup_name,
            "vision": startup_vision,
            "completed_tasks": completed_tasks,
            "current_open_tasks": current_open_tasks,
        }
        user_prompt = json.dumps(user_payload, ensure_ascii=True)

        raw = self._chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
        return validate_iteration_plan(parse_json_strict(raw))

    def _chat_json(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI chat completion with deterministic JSON output."""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned empty response content")
        return content
