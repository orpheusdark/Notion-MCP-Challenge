"""CLI entrypoint for AI Startup Operator."""

from __future__ import annotations

import sys

from ai_agent import AIAgent
from config import load_settings
from notion_api_client import NotionStartupClient
from utils import ValidationError, comma_split


def run() -> None:
    """Run the CLI orchestration workflow end-to-end."""
    print("AI Startup Operator (Notion as Operating System)")
    print("-" * 52)

    try:
        settings = load_settings()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        sys.exit(1)

    ai = AIAgent(settings)
    notion = NotionStartupClient(settings)

    idea = input("Enter your startup idea: ").strip()
    if not idea:
        print("Startup idea cannot be empty.")
        sys.exit(1)

    try:
        initial = ai.generate_initial_plan(idea)
    except ValidationError as exc:
        print(f"AI output validation error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"Failed to generate startup plan: {exc}")
        sys.exit(1)

    startup_name = initial["startup_name"]
    startup_title = f"Startup Dashboard - {startup_name}"

    try:
        dashboard_page_id = notion.create_page(startup_title)
        notion.append_dashboard_content(
            page_id=dashboard_page_id,
            vision=initial["vision"],
            key_features=initial["key_features"],
            roadmap=initial["roadmap"],
        )

        tasks_db_id = notion.create_database(
            parent_page_id=dashboard_page_id,
            title="Tasks",
        )

        for task in initial["tasks"]:
            notion.add_task(tasks_db_id, task)
    except Exception as exc:
        print(f"Failed to write startup data to Notion: {exc}")
        sys.exit(1)

    print(f"Created startup dashboard: {startup_title}")
    print("Initial tasks were added to Notion.")

    while True:
        completed_raw = input(
            "What tasks did you complete? (comma-separated, or 'none', or 'exit'): "
        ).strip()

        if completed_raw.lower() in {"exit", "quit"}:
            print("Exiting update loop.")
            break

        completed_tasks = comma_split(completed_raw)
        if completed_tasks:
            for completed_title in completed_tasks:
                try:
                    task_page_id = notion.find_task_page_id(tasks_db_id, completed_title)
                    if task_page_id is None:
                        print(f"Task not found in Notion: {completed_title}")
                        continue
                    notion.update_task_status(task_page_id, "Done")
                    print(f"Marked as Done: {completed_title}")
                except Exception as exc:
                    print(f"Failed to update task '{completed_title}': {exc}")

        try:
            open_tasks = notion.get_open_task_titles(tasks_db_id)
            iteration = ai.generate_next_iteration(
                startup_name=startup_name,
                startup_vision=initial["vision"],
                completed_tasks=completed_tasks,
                current_open_tasks=open_tasks,
            )
        except ValidationError as exc:
            print(f"AI output validation error on iteration: {exc}")
            continue
        except Exception as exc:
            print(f"Failed to generate next iteration plan: {exc}")
            continue

        print("\nSuggestions:")
        for suggestion in iteration["suggestions"]:
            print(f"- {suggestion}")

        print("\nAdding next tasks to Notion:")
        for task in iteration["next_tasks"]:
            try:
                notion.add_task(tasks_db_id, task)
                print(
                    f"- Added: {task['title']} "
                    f"(Priority: {task['priority']}, Status: {task['status']})"
                )
            except Exception as exc:
                print(f"- Failed to add task '{task['title']}': {exc}")

        print()


if __name__ == "__main__":
    run()
