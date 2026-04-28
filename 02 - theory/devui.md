# DevUI — Microsoft Agent Framework

> Source: https://learn.microsoft.com/en-us/agent-framework/devui/?pivots=programming-language-python

---

## What is DevUI?

DevUI is a **lightweight, standalone sample application** for running agents and workflows locally during development. It provides:

- A web interface for interactive testing
- An OpenAI-compatible REST API backend
- Visual debugging and tracing via OpenTelemetry

> **Important**: DevUI is a development tool — it is **not intended for production use**.

---

## Features

| Feature | Description |
|---|---|
| Web Interface | Interactive browser UI for testing agents and workflows |
| Flexible Input Types | Auto-generates forms based on the workflow's first executor input type |
| In-Memory Registration | Register entities programmatically — no file system setup needed |
| Directory Discovery | Automatically discover agents/workflows from a folder structure |
| OpenAI-Compatible API | Use the OpenAI Python SDK to talk to your local agents |
| Sample Gallery | Browse curated examples when no entities are found |
| Tracing | View OpenTelemetry traces for debugging and observability |

---

## Installation

```bash
pip install agent-framework-devui --pre
```

---

## Quick Start

### Option 1 — Programmatic Registration (recommended for exercises)

Register agents and workflows in code and launch the server:

```python
from agent_framework import Agent
from agent_framework.devui import serve

agent = Agent(name="MyAgent", client=..., tools=[...])

serve(entities=[agent], port=8080, auto_open=True)
# Opens http://localhost:8080 in your browser
```

For a workflow:

```python
from agent_framework.devui import serve

workflow = create_workflow()   # returns a built Workflow object
serve(entities=[workflow], port=8080, auto_open=False)
```

### Option 2 — Directory Discovery (CLI)

If agents and workflows are organised in a folder:

```bash
devui ./agents --port 8080
# Web UI:  http://localhost:8080
# API:     http://localhost:8080/v1/*
```

---

## Input Types

DevUI adapts the input form to the entity type:

- **Agents** — text box + optional file attachments (images, documents)
- **Workflows** — form fields are auto-generated from the first executor's input dataclass

This means that if your workflow starts with a `@dataclass` like `SAPIncident`, DevUI will render a form with one field per attribute — no extra configuration needed.

---

## Using the OpenAI SDK against DevUI

DevUI exposes an OpenAI-compatible Responses API. You can drive it programmatically:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed",          # no auth required for local DevUI
)

response = client.responses.create(
    metadata={"entity_id": "MyAgent"},   # agent or workflow name
    input="What is the status of PRD?",
)

print(response.output[0].content[0].text)
```

---

## CLI Options

```bash
devui [directory] [options]

Options:
  --port, -p      Port to listen on (default: 8080)
  --host          Host to bind to (default: 127.0.0.1)
  --headless      API only, no web UI
  --no-open       Don't automatically open the browser
  --tracing       Enable OpenTelemetry tracing
  --reload        Enable auto-reload on file changes
  --mode          developer | user  (default: developer)
  --auth          Enable Bearer token authentication
  --auth-token    Custom authentication token
```

---

## Key Takeaways

- `serve(entities=[...])` is the fastest way to launch DevUI from a Python script.
- The form UI is automatically derived from your first executor's input type — use dataclasses for clean forms.
- DevUI is for **development only** — for production, expose your workflow via Azure Functions, a FastAPI app, or another host.
- The OpenAI-compatible API lets you drive DevUI from notebooks, scripts, or other tools without opening the browser.

---

## References

- [DevUI overview](https://learn.microsoft.com/en-us/agent-framework/devui/)
- [Directory Discovery](https://learn.microsoft.com/en-us/agent-framework/devui/directory-discovery)
- [API Reference](https://learn.microsoft.com/en-us/agent-framework/devui/api-reference)
- [Tracing & Observability](https://learn.microsoft.com/en-us/agent-framework/devui/tracing)
- [Security & Deployment](https://learn.microsoft.com/en-us/agent-framework/devui/security)
- [Samples](https://learn.microsoft.com/en-us/agent-framework/devui/samples)
