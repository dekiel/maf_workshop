# Microsoft Agent Framework Workshop — Python for SAP Developers

> A hands-on, progressive workshop for the SAP developer community.  
> Build AI agents and workflows that automate real SAP scenarios using the **Microsoft Agent Framework (MAF)** for Python.

---

## Workshop Overview

| | |
|---|---|
| **Duration** | ~4 hours (self-paced) |
| **Audience** | SAP developers with Python basics |
| **Level** | Intermediate |
| **Runtime** | Python 3.10+ |
| **AI backend** | Azure AI Foundry **or** GitHub Models (gpt-4o recommended) |

### What you will build

| Exercise | Topic | SAP Scenario |
|---|---|---|
| [ex00-setup](exercises/ex00-setup/) | Environment validation | — |
| [ex01-basic-agent](exercises/ex01-basic-agent/) | Your first MAF agent | SAP system health checker |
| [ex02-agent-mcp](exercises/ex02-agent-mcp/) | Agent with MCP tools | Query SAP documentation via GitHub MCP |
| [ex03-basic-workflow](exercises/ex03-basic-workflow/) | Basic workflow | SAP incident triage pipeline |
| [ex04-hitl-checkpoint](exercises/ex04-hitl-checkpoint/) | Human-in-the-loop + checkpoints | SAP change request approval workflow |

### Learning outcomes
- Understand the MAF core primitives: `Agent`, `tool`, `WorkflowBuilder`, `Executor`
- Connect agents to external tools and MCP servers
- Build sequential and parallel multi-agent workflows
- Implement human approval gates with checkpoint/resume
- Design a full end-to-end scenario matching real customer scenarios
---

## Prerequisites

### Required tools
| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime |
| pip | latest | Package manager |
| Azure CLI (`az`) | latest | Azure authentication |
| VS Code | latest | Recommended IDE |
| Git | any | Clone samples |

### Required accounts / access
At least **one** of the following:

**Option A — Azure AI Foundry** (required for Exercise 02)
- Azure subscription with an Azure AI Foundry project provisioned ([quickstart](https://learn.microsoft.com/azure/ai-foundry/))
- A model deployment (e.g., `gpt-4o`) in that project
- `az login` completed

**Option B — GitHub Models** (all exercises except 02)
- A GitHub Personal Access Token ([create one](https://github.com/settings/tokens)) — scopes: `read:user`

### Python knowledge assumed
- Functions, classes, `async/await`
- `pip install` and virtual environments
- Basic familiarity with decorators

---

## Installation

### 1 — Clone this repository
```bash
git clone https://github.com/your-org/maf_workshop.git
cd maf_workshop
```

### 2 — Create a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### 4 — Configure environment variables
```bash
cp .env.example .env
# Then open .env and fill in your values
```

**Option A — Azure AI Foundry:**
```
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=gpt-4o
```

**Option B — GitHub Models:**
```
GITHUB_PAT=github_pat_...
GITHUB_MODEL=gpt-4o
```

### 5 — Authenticate with Azure *(Foundry only — skip for GitHub Models)*
```bash
az login
```

### 6 — Verify your setup
```bash
python exercises/ex00-setup/verify_setup.py
```
Expected output (Foundry):
```

---

## Exercise Guide

### Ex00 — Setup Validation
**Goal:** Confirm tools, credentials and LLM connectivity before starting.  
**Concepts:** `create_chat_client()`, Azure AI Foundry auth, GitHub Models auth, env var priority order

---

### Ex01 — Basic Agent: SAP System Health Checker
**Goal:** Build an agent that answers SAP Basis questions by calling Python tools — check system status, list incidents, create a support message.  
**Concepts:** `Agent`, `@tool`, `create_chat_client()`, streaming responses, `approval_mode`

---

### Ex02 — Agent with MCP: SAP Notes Researcher
**Goal:** Extend an agent with a remote MCP server so it can search GitHub repositories and issues without any custom API wrappers.  
**Concepts:** `client.get_mcp_tool()`, MCP transports, `async with Agent(...)`, mixing local `@tool` and remote MCP tools

> Requires Foundry — `get_mcp_tool()` is not available on the GitHub Models backend.

---

### Ex03 — Basic Workflow: SAP Incident Triage Pipeline
**Goal:** Chain multiple deterministic steps into a workflow that classifies, enriches and drafts a resolution plan for an SAP incident.  
**Concepts:** `WorkflowBuilder`, `Executor`, `@executor`, `@handler`, `ctx.send_message()`, `ctx.yield_output()`

---

### Ex04 — HITL + Checkpoints: SAP Change Request Approval
**Goal:** Build a workflow that pauses at a human approval gate, persists its state to disk, and resumes after a restart.  
**Concepts:** `ctx.request_info()`, `@response_handler`, `FileCheckpointStorage`, checkpoint save/restore, workflow resume

---

### Ex05 — Complex Scenario: RISE with SAP Readiness Assessment
**Goal:** Combine multiple agents, shared workflow state, a human sign-off gate and file output into a production-grade end-to-end assessment pipeline.  
**Concepts:** `AgentExecutor`, multi-agent pipeline, `ctx.set_state` / `ctx.get_state`, HITL checkpoint, output to file

---

### Ex06 — Dev UI: SAP Triage with Browser Interface
**Goal:** Register agents and a workflow in the MAF Developer UI to interact with them visually in the browser and inspect traces.  
**Concepts:** `serve(entities=[...])`, DevUI form auto-generation from dataclasses, OpenTelemetry traces, parallel workflow branches

---

## Project structure

```
maf_workshop/
├── README.md
├── requirements.txt
├── .env.example
├── setup/
│   └── instructions.md
├── exercises/
│   ├── ex00-setup/
│   │   └── verify_setup.py
│   ├── ex01-basic-agent/
│   │   ├── README.md
│   │   └── sap_health_agent.py
│   ├── ex02-agent-mcp/
│   │   ├── README.md
│   │   └── sap_notes_agent.py
│   ├── ex03-basic-workflow/
│   │   ├── README.md
│   │   └── incident_triage_workflow.py
│   ├── ex04-hitl-checkpoint/
│   │   ├── README.md
│   │   └── change_request_workflow.py
│   ├── ex05-complex-scenario/
│   │   ├── README.md
│   │   └── rise_assessment_workflow.py
│   ├── ex06-devui/
│   │   ├── README.md
│   │   ├── sap_triage_devui.py
│   │   └── checkpoints/
│   └── shared/
│       ├── __init__.py
│       └── model_client.py

```

---

## How to reset / clean up

```bash
# Remove checkpoint files created by ex04, ex05 and ex06
rm -rf exercises/ex04-hitl-checkpoint/checkpoints/
rm -rf exercises/ex05-complex-scenario/checkpoints/
rm -rf exercises/ex06-devui/checkpoints/
rm -rf output/

# Deactivate virtual environment
deactivate
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: agent_framework` | Package not installed | Run `pip install -r requirements.txt` |
| `DefaultAzureCredential failed` | Not logged in | Run `az login` |
| `FOUNDRY_PROJECT_ENDPOINT not set` | Missing `.env` | Copy `.env.example` → `.env` and fill values (or use `GITHUB_PAT` instead) |
| `get_mcp_tool` not found | Using GitHub Models for ex02 | Ex02 requires Foundry — set `FOUNDRY_PROJECT_ENDPOINT` |
| `HTTP 401 from Foundry` | Wrong endpoint or model name | Check your Azure AI Foundry project URL |
| `GITHUB_PAT not set` (ex02) | Missing token | Create token at github.com/settings/tokens |
| `FileCheckpointStorage` path error | Directory missing | The code creates it; ensure you have write permission |
| Agent hangs waiting for input | HITL prompt shown | Read the console — type `approve` or feedback |

---

## Additional Resources

- [Microsoft Agent Framework — Microsoft Learn](https://learn.microsoft.com/azure/developer/agent-framework/)
- [agent-framework Python samples on GitHub](https://github.com/microsoft/agent-framework/tree/main/python/samples)
- [Azure AI Foundry quickstart](https://learn.microsoft.com/azure/ai-foundry/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

---

