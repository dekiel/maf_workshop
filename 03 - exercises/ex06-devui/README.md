# Exercise 06 — DevUI: Visualise Agents & Workflows in the Browser

## Goal
Build a multi-step SAP incident triage workflow and visualise it live in the browser using the MAF DevUI.
The workflow runs parallel classification and system enrichment, sends the result to an LLM for a resolution plan, routes to an early stop if there is not enough context, and otherwise pauses for human approval before confirming execution.

## What is DevUI?
Launch the **Microsoft Agent Framework DevUI** — a browser-based interface that
lets you interact with agents and workflows visually, inspect traces, and test
structured inputs without writing any extra code.
DevUI is a lightweight development tool that:
- Provides a **web chat UI** for conversational agents
- Auto-generates an **input form** for workflows based on the input dataclass
- Shows **OpenTelemetry traces** for every step
- Exposes an **OpenAI-compatible API** so you can also call agents programmatically

> DevUI is for development only — not intended for production.

## Workflow architecture

```
SAPIncident (form input)
    │
    ▼
ParallelAnalysisExecutor   ← _classify() + _enrich() run in parallel (asyncio.gather)
    │                          produces: SAP component, category, priority, system health
    ▼
PlanRouter                 ← checks if the incident has enough information (no LLM call yet)
    │  not enough info → yield_output (workflow ends here)
    │  enough info     → forward to ResolutionPlanner
    ▼
ResolutionPlanner          ← AgentExecutor: LLM drafts a resolution plan (max 200 words)
    │
    ▼
ApprovalGateway (HITL)     ← pauses workflow; human types 'approve' or provides feedback
    │  approved → send_message
    │  rejected → yield_output (workflow ends here)
    ▼
ConfirmationExecutor       ← emits '✅ Resolution plan started' with full plan
```

DevUI reads the `SAPIncident` dataclass and **automatically generates a form**
with fields for `incident_id`, `system_id`, `short_text`, `long_text`, and `reported_by`.

## Run
```
python exercises/ex06-devui/sap_triage_devui.py
```

The browser opens at **http://localhost:8080**.

## What to try

**Select `IncidentTriageWithApproval`** and fill in the form.

**Happy path** (meaningful incident, gets to approval):
- Incident ID: `INC-001`
- System ID: `PRD`
- Short Text: `Work processes are all in PRIV mode, system unresponsive`
- Long Text: `All dialog work processes are in PRIV status since 08:00. Users cannot log in.`
- Reported By: `basis-team`

Hit **Run**, wait for the plan, then type `approve` when prompted.

**Insufficient info path** (workflow stops at PlanRouter):
- Incident ID: `INC-002`
- System ID: `DEV`
- Short Text: `Something is wrong`
- Long Text: *(leave blank)*
- Reported By: `user1`

The workflow stops before reaching the approval gate.

Click **Traces** in the sidebar to see each step's input and output.

## Key concepts demonstrated

- `serve(entities=[...])` — one call registers agents and workflows in DevUI
- DevUI introspects the first executor's input dataclass to auto-generate the form
- `asyncio.gather()` — parallel execution of independent coroutines in one step
- `PlanRouter` — conditional branching: early exit or forward based on LLM output
- `request_info` / `response_handler` — HITL pause and resume pattern
- Traces show each executor's input, output, and LLM messages

## Stop
Press `Ctrl+C` in the terminal.
