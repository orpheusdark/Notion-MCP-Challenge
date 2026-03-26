# AI Startup Operator (Notion as Operating System)

A production-ready CLI system that turns a startup idea into an operating dashboard in Notion.

The app uses OpenAI to generate structured startup plans and task backlogs, then uses the Notion API to create and maintain your startup workspace.

## Features

- CLI prompt: capture a startup idea in one line
- Deterministic AI planning with strict JSON output
- Automatic Notion setup:
  - creates a Startup Dashboard page
  - creates a Tasks database with `Name`, `Status`, and `Priority`
- Auto-population of dashboard content:
  - vision
  - key features
  - roadmap phases
- Auto-population of initial tasks
- Continuous update loop:
  - mark completed tasks in Notion
  - ask AI for next tasks and suggestions
  - append new tasks to Notion
- Environment-based configuration with `.env`
- Validation and robust error handling for AI and API responses

## Project Structure

```text
startup-operator/
├── main.py
├── ai_agent.py
├── notion_api_client.py
├── config.py
├── utils.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- OpenAI API key
- Notion internal integration token
- A Notion parent page shared with your integration

## Setup

1. Clone or open the project folder.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the `startup-operator` folder:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
NOTION_API_KEY=your_notion_integration_secret
NOTION_PARENT_PAGE_ID=your_notion_parent_page_id
```

## Notion Preparation

1. Create an internal integration in Notion.
2. Copy the integration secret into `NOTION_API_KEY`.
3. Create or choose a Notion page to act as your parent page.
4. Share that page with your integration.
5. Copy the page ID into `NOTION_PARENT_PAGE_ID`.

## How to Run

From the `startup-operator` directory:

```bash
python main.py
```

Then follow CLI prompts.

## Example Usage

```text
AI Startup Operator (Notion as Operating System)
----------------------------------------------------
Enter your startup idea: AI agent that automates customer onboarding for SaaS
Created startup dashboard: Startup Dashboard - OnboardPilot
Initial tasks were added to Notion.
What tasks did you complete? (comma-separated, or 'none', or 'exit'): Define MVP scope, Set up onboarding personas
Marked as Done: Define MVP scope
Marked as Done: Set up onboarding personas

Suggestions:
- Validate onboarding assumptions with 5 pilot users.
- Define measurable onboarding success metrics.
- Prioritize integration reliability over feature breadth.

Adding next tasks to Notion:
- Added: Build onboarding checklist generator (Priority: High, Status: Not Started)
- Added: Instrument activation funnel analytics (Priority: Medium, Status: Not Started)
- Added: Draft pilot feedback interview script (Priority: Low, Status: Not Started)
```

## Architecture

- `main.py`
  - CLI entrypoint
  - Orchestrates full workflow and update loop
  - Handles user interactions and top-level errors

- `ai_agent.py`
  - Encapsulates OpenAI API calls
  - Uses deterministic generation (`temperature=0`)
  - Enforces JSON-only responses with strict schema prompts

- `notion_api_client.py`
  - Encapsulates Notion API calls using official `notion-client`
  - Creates dashboard page and tasks database
  - Adds and updates tasks

- `config.py`
  - Loads environment variables via `python-dotenv`
  - Validates required configuration

- `utils.py`
  - Strict JSON parsing and schema validation
  - Task normalization for `Priority` and `Status`
  - Helper for parsing comma-separated completion input

## Design Notes

- JSON Strictness:
  - The OpenAI call requests JSON object output only.
  - Responses are parsed with strict JSON loading.
  - Schema fields are validated and normalized before any Notion writes.

- Reliability:
  - Fail-fast behavior on configuration and API errors.
  - Per-task exception handling during update loop avoids total failure.

- Extensibility:
  - The architecture cleanly separates orchestration, AI logic, Notion I/O, and validation.
  - You can add metrics, additional Notion databases, or memory/state persistence without major rewrites.
