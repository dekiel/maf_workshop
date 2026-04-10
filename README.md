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
| **AI backend** | Azure AI Foundry (gpt-4o recommended) |

### What you will build

| Exercise | Topic | SAP Scenario |
|---|---|---|
| [ex00-setup](exercises/ex00-setup/) | Environment validation | — |
| [ex01-basic-agent](exercises/ex01-basic-agent/) | Your first MAF agent | SAP system health checker |
| [ex02-agent-mcp](exercises/ex02-agent-mcp/) | Agent with MCP tools | Query SAP documentation via GitHub MCP |
| [ex03-basic-workflow](exercises/ex03-basic-workflow/) | Basic workflow | SAP incident triage pipeline |
| [ex04-hitl-checkpoint](exercises/ex04-hitl-checkpoint/) | Human-in-the-loop + checkpoints | SAP change request approval workflow |
| [ex05-complex-scenario](exercises/ex05-complex-scenario/) | Agent + workflow combined | End-to-end RISE with SAP assessment |

### Learning outcomes
- Understand the MAF core primitives: `Agent`, `tool`, `WorkflowBuilder`, `Executor`
- Connect agents to external tools and MCP servers
- Build sequential and parallel multi-agent workflows
- Implement human approval gates with checkpoint/resume
- Design a full end-to-end scenario matching real SAP operations

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
- **Azure subscription** with an Azure AI Foundry project provisioned ([quickstart](https://learn.microsoft.com/azure/ai-foundry/))
- A **model deployment** (e.g., `gpt-4o`) in that project
- *(Exercise 02 only)* A GitHub Personal Access Token ([create one](https://github.com/settings/tokens))

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

Minimum required variables for most exercises:
```
FOUNDRY_PROJECT_ENDPOINT=https://<your-project>.services.ai.azure.com/api/projects/<your-project>
FOUNDRY_MODEL=gpt-4o
```

### 5 — Authenticate with Azure
```bash
az login
```

### 6 — Verify your setup
```bash
python exercises/ex00-setup/verify_setup.py
```
Expected output:
```
✅ Python version OK: 3.xx
✅ agent_framework package found
✅ Azure CLI credential OK
✅ Foundry endpoint reachable
All checks passed — you are ready to start!
```

---

## Exercise Guide

### Ex00 — Setup Validation
**Goal:** Confirm that all tools and credentials are working.  
**File:** [exercises/ex00-setup/verify_setup.py](exercises/ex00-setup/verify_setup.py)  
```bash
python exercises/ex00-setup/verify_setup.py
```

---

### Ex01 — Basic Agent: SAP System Health Checker
**Goal:** Create your first MAF agent with a `@tool` function.  
**File:** [exercises/ex01-basic-agent/sap_health_agent.py](exercises/ex01-basic-agent/sap_health_agent.py)

```bash
python exercises/ex01-basic-agent/sap_health_agent.py
```

**Concepts:** `Agent`, `FoundryChatClient`, `@tool`, streamed responses  
**Verification:** The agent responds to questions like *"What is the status of PRD?"* using a mock SAP landscape tool.

---

### Ex02 — Agent with MCP: SAP Notes Researcher
**Goal:** Connect to a remote MCP server (GitHub) and extend the agent with live tool discovery.  
**File:** [exercises/ex02-agent-mcp/sap_notes_agent.py](exercises/ex02-agent-mcp/sap_notes_agent.py)

Additional setup — set in `.env`:
```
GITHUB_PAT=<your-github-pat>
OPENAI_API_KEY=<your-openai-key>     # or use FOUNDRY env vars
OPENAI_MODEL=gpt-4o
```

```bash
python exercises/ex02-agent-mcp/sap_notes_agent.py
```

**Concepts:** `client.get_mcp_tool()`, remote MCP server, `async with Agent(...)`, dynamic tool registration  
**Verification:** Agent queries GitHub repositories and issues related to SAP-themed topics.

---

### Ex03 — Basic Workflow: SAP Incident Triage Pipeline
**Goal:** Chain multiple processing steps into a deterministic workflow.  
**File:** [exercises/ex03-basic-workflow/incident_triage_workflow.py](exercises/ex03-basic-workflow/incident_triage_workflow.py)

```bash
python exercises/ex03-basic-workflow/incident_triage_workflow.py
```

**Concepts:** `WorkflowBuilder`, `Executor`, `@executor`, `@handler`, edges, `ctx.send_message()`, `ctx.yield_output()`  
**Verification:** A sample SAP incident is classified, enriched, and a response draft is produced.

---

### Ex04 — HITL + Checkpoints: SAP Change Request Approval
**Goal:** Build a workflow that pauses for human approval and can be checkpointed and resumed.  
**File:** [exercises/ex04-hitl-checkpoint/change_request_workflow.py](exercises/ex04-hitl-checkpoint/change_request_workflow.py)

```bash
python exercises/ex04-hitl-checkpoint/change_request_workflow.py
```

**Concepts:** `ctx.request_info()`, `@response_handler`, `FileCheckpointStorage`, `on_checkpoint_save/restore`, resume from checkpoint  
**Verification:** The workflow pauses, prompts for approval, and the approved change request is processed through to completion. After approval, you will see a checkpoint resume prompt.

---

### Ex05 — Complex Scenario: RISE with SAP Readiness Assessment
**Goal:** Combine a multi-agent orchestration workflow with an integrated sub-workflow, MCP-powered research, and a human sign-off gate.  
**File:** [exercises/ex05-complex-scenario/rise_assessment_workflow.py](exercises/ex05-complex-scenario/rise_assessment_workflow.py)

```bash
python exercises/ex05-complex-scenario/rise_assessment_workflow.py
```

**Concepts:** Multi-agent handoff, `WorkflowBuilder` composition, `AgentExecutor`, state management, human approval, output aggregation  
**Verification:** The assessment workflow produces a RISE readiness report, pauses for human sign-off, and saves the result to `output/assessment_report.md`.

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
│   └── ex05-complex-scenario/
│       ├── README.md
│       └── rise_assessment_workflow.py
└── solutions/
    ├── ex01_solution.py
    ├── ex02_solution.py
    ├── ex03_solution.py
    ├── ex04_solution.py
    └── ex05_solution.py
```

---

## How to reset / clean up

```bash
# Remove checkpoint files created by ex04 and ex05
rm -rf exercises/ex04-hitl-checkpoint/checkpoints/
rm -rf exercises/ex05-complex-scenario/checkpoints/
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
| `FOUNDRY_PROJECT_ENDPOINT not set` | Missing `.env` | Copy `.env.example` → `.env` and fill values |
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

*Workshop content created for the SAP developer technical community — April 2026.*
