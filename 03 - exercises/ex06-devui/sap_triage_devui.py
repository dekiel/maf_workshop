"""
Exercise 06 — DevUI + Parallel + HITL: SAP Incident Triage with Human Approval

Like Exercise 03, but with three key changes:

  Change 1 — PARALLEL
      IncidentClassifier and SystemEnricher run at the same time (asyncio.gather),
      instead of sequentially. Both receive the raw incident and produce independent
      results that are merged before the next step.

  Change 2 — HUMAN APPROVAL
      After the LLM produces a resolution plan, the workflow PAUSES and asks a
      human to approve. Type 'approve' in the DevUI to continue.

  Change 3 — CONFIRMATION
      On approval, the final step emits: "Resolution plan started"

Workflow:
  SAPIncident
    → Step 1 — ParallelAnalysisExecutor  : Classifier + Enricher (parallel)
    → Step 2 — ResolutionPlanner (LLM)   : drafts the resolution plan
    → Step 3 — ApprovalGateway (HITL)    : human reviews and approves
    → Step 4 — ConfirmationExecutor      : emits "Resolution plan started"

Run:
  python exercises/ex06-devui/sap_triage_devui.py
  → opens http://localhost:8080

References
----------
- DevUI docs   : https://learn.microsoft.com/en-us/agent-framework/devui/
- Parallel      : https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows
- HITL sample  : https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/human-in-the-loop/
"""

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework import (
    Agent,
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)
from agent_framework.devui import serve
from dotenv import load_dotenv
from shared.model_client import create_chat_client

load_dotenv()


# Define Data Classes for Incident, Analysis Result, and Approval Request
@dataclass
class SAPIncident:
    """Raw incoming SAP support incident. DevUI auto-generates a form from these fields."""
    incident_id: str
    system_id: str      # e.g. PRD, QAS, DEV, SBX
    short_text: str
    long_text: str
    reported_by: str

@dataclass
class AnalysisResult:
    """Combined result of parallel classification + enrichment."""
    incident: SAPIncident
    sap_component: str
    incident_category: str
    responsible_team: str
    suggested_priority: str
    system_status: str
    system_cpu_pct: int
    system_mem_pct: int

@dataclass
class ApprovalRequest:
    """Structured human-in-the-loop pause: presented to the approver in DevUI."""
    prompt: str
    incident_id: str
    priority: str
    plan: str


# Classification and enrichment logic mimicking real-world complexity with fake system status DB
_COMPONENT_MAP = {
    "work process": ("BC-SYS", "System Down", "SAP Basis"),
    "transport":    ("BC-CTS", "Transport", "SAP Basis"),
    "authoris":     ("BC-SEC", "Authorisation", "Security Team"),
    "authorization":("BC-SEC", "Authorisation", "Security Team"),
    "cpu":          ("BC-OP-NT", "Performance", "SAP Basis"),
    "performance":  ("BC-OP-NT", "Performance", "SAP Basis"),
    "memory":       ("BC-OP-NT", "Performance", "SAP Basis"),
    "billing":      ("SD-BIL", "Finance & SD", "SD/FI Team"),
    "payment":      ("FI-FBL", "Finance", "FI Team"),
    "fiori":        ("EP-PIN-FRW", "Fiori / UI5", "UX Team"),
    "odata":        ("BC-ESI-WS", "OData / API", "Integration Team"),
    "rfc":          ("BC-MID-RFC", "RFC / Middleware", "Integration Team"),
}

_SYSTEM_STATUS_DB = {
    "PRD": {"status": "GREEN",   "cpu_pct": 42, "mem_pct": 67},
    "QAS": {"status": "YELLOW",  "cpu_pct": 78, "mem_pct": 82},
    "DEV": {"status": "GREEN",   "cpu_pct": 15, "mem_pct": 44},
    "SBX": {"status": "RED",     "cpu_pct": 95, "mem_pct": 91},
}

# Classifier logic
async def _classify(incident: SAPIncident) -> tuple[str, str, str, str]:
    """Keyword-based SAP component classifier → (component, category, team, priority)."""
    text = (incident.short_text + " " + incident.long_text).lower()
    component, category, team = "", "", ""
    for keyword, mapping in _COMPONENT_MAP.items():
        if keyword in text:
            component, category, team = mapping
            break
    priority = "P1" if ("down" in text or "cannot" in text) else "P2"
    print(f"  ├─ [Classifier]  Component={component} | Category={category} | Priority={priority}")
    return component, category, team, priority

# Enricher logic
async def _enrich(incident: SAPIncident) -> tuple[str, int, int]:
    """Live system health look-up → (status, cpu_pct, mem_pct)."""
    metrics = _SYSTEM_STATUS_DB.get(
        incident.system_id.upper(),
        {"status": "UNKNOWN", "cpu_pct": 0, "mem_pct": 0},
    )
    print(
        f"  ├─ [Enricher]    {incident.system_id} status={metrics['status']}, "
        f"CPU={metrics['cpu_pct']}%, MEM={metrics['mem_pct']}%"
    )
    return metrics["status"], metrics["cpu_pct"], metrics["mem_pct"]


# Step 1 — ParallelAnalysisExecutor
# CHANGE 1: runs _classify() and _enrich() at the same time with asyncio.gather()

class ParallelAnalysisExecutor(Executor):
    """
    Runs IncidentClassifier and SystemEnricher IN PARALLEL using asyncio.gather().
    Both coroutines receive the same Incident independently; their results
    are merged into a single AnalysisResult before the next step.
    """

    def __init__(self) -> None:
        super().__init__(id="parallel_analysis")

    @handler
    async def analyse(
        self,
        incident: SAPIncident,
        ctx: WorkflowContext[AgentExecutorRequest],
    ) -> None:
        print(f"\n  Step 1 — Parallel analysis (classifying + enriching simultaneously)...")

        # PARALLEL EXECUTION
        (component, category, team, priority), (status, cpu, mem) = await asyncio.gather(
            _classify(incident),
            _enrich(incident),
        )

        analysis = AnalysisResult(
            incident=incident,
            sap_component=component,
            incident_category=category,
            responsible_team=team,
            suggested_priority=priority,
            system_status=status,
            system_cpu_pct=cpu,
            system_mem_pct=mem,
        )
        ctx.set_state("analysis", analysis)

        prompt = (
            f"You are an SAP Basis expert. Produce a concise resolution plan (max 200 words) for the following incident.\n\n"
            f"Incident ID    : {incident.incident_id}\n"
            f"System         : {incident.system_id} - currently {status} "
            f"(CPU {cpu}%, MEM {mem}%)\n"
            f"SAP Component  : {component}\n"
            f"Category       : {category}\n"
            f"Priority       : {priority}\n"
            f"Responsible    : {team}\n\n"
            f"Problem description:\n{incident.short_text}\n\n"
            f"{incident.long_text}\n\n"
            f"Provide:\n"
            f"1. Root cause hypothesis\n"
            f"2. Immediate containment steps (SAP t-codes)\n"
            f"3. Long-term fix recommendation\n"
        )

        print(f"  Step 2 — Sending to Resolution Planner (LLM)...")
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[Message("user", contents=[prompt])],
                should_respond=True,
            )
        )

# Step 2 — PlanRouter: checks incident content BEFORE calling the LLM

class PlanRouter(Executor):
    """
    Sits between ParallelAnalysisExecutor and ResolutionPlanner.
    Checks whether the incident description contains enough information.
    If not → stops the workflow immediately (no LLM call is made).
    If yes → forwards the AgentExecutorRequest to ResolutionPlanner.
    """

    _MIN_WORDS = 5

    def __init__(self) -> None:
        super().__init__(id="plan_router")

    @handler
    async def route(
        self,
        request: AgentExecutorRequest,
        ctx: WorkflowContext[AgentExecutorRequest, str],
    ) -> None:
        analysis: AnalysisResult = ctx.get_state("analysis")
        combined = analysis.incident.short_text + " " + analysis.incident.long_text
        words = [w for w in combined.split() if w.isalpha()]
        if len(words) < self._MIN_WORDS:
            print(f"\n  Step 2 — ⛔ Insufficient information — stopping workflow (no LLM call)")
            await ctx.yield_output(
                f"⚠️ Workflow stopped: not enough information to produce a resolution plan.\n\n"
                f"**Incident ID**: {analysis.incident.incident_id}  \n"
                f"**System**: {analysis.incident.system_id}  \n"
                f"**SAP Component**: {analysis.sap_component}  \n"
                f"**Category**: {analysis.incident_category}  \n"
                f"**Priority**: {analysis.suggested_priority}  \n\n"
                f"---"
            )
        else:
            print(f"\n  Step 2 — ✅ Incident has enough info — forwarding to LLM planner")
            await ctx.send_message(request)


# Step 4 - ApprovalGateway  (HITL) - workflow pauses here for human approval

class ApprovalGateway(Executor):
    """
    Human-in-the-loop checkpoint.
    The workflow pauses and presents the resolution plan to the approver.
    In DevUI: a prompt appears asking for your decision.
    Type 'approve' to proceed, or any other text to decline.
    """

    def __init__(self) -> None:
        super().__init__(id="approval_gateway")

    @handler
    async def on_plan(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext[None, str],
    ) -> None:
        analysis: AnalysisResult = ctx.get_state("analysis")
        plan_text = response.agent_response.text
        ctx.set_state("plan", plan_text)

        print(f"\n  Step 4 — ⏸  Human approval required — pausing workflow (HITL)")  # noqa: E501
        await ctx.request_info(
            request_data=ApprovalRequest(
                prompt=(
                    "Review the resolution plan and type 'approve' to start it, "
                    "or describe the changes needed."
                ),
                incident_id=analysis.incident.incident_id,
                priority=analysis.suggested_priority,
                plan=plan_text,
            ),
            response_type=str,
        )

    @response_handler
    async def on_decision(
        self,
        original_request: ApprovalRequest,
        decision: str,
        ctx: WorkflowContext[str],
    ) -> None:
        if decision.strip().lower() in ("approve", "yes", "y", "ok"):
            print(f"  Step 4 — ✅ Approved — continuing to confirmation")
            await ctx.send_message("approved")
        else:
            print(f"  Step 4 — ❌ Not approved — stopping workflow")
            await ctx.yield_output(
                f"Resolution plan was NOT approved.\n\nFeedback received: {decision}"
            )

# Step 4 - ConfirmationExecutor - emits "Resolution plan started"
class ConfirmationExecutor(Executor):
    """Emits the final 'Resolution plan started' confirmation message."""

    def __init__(self) -> None:
        super().__init__(id="confirmation")

    @handler
    async def confirm(
        self,
        _: str,
        ctx: WorkflowContext[None, str],
    ) -> None:
        analysis: AnalysisResult = ctx.get_state("analysis")
        plan: str = ctx.get_state("plan")

        output = (
            f"✅ Resolution plan started\n\n"
            f"**Incident**: {analysis.incident.incident_id}  "
            f"**System**: {analysis.incident.system_id}  "
            f"**Priority**: {analysis.suggested_priority}\n\n"
            f"---\n\n{plan}"
        )
        print(f"  Step 4 — Resolution plan started.")
        await ctx.yield_output(output)


# Workflow assembly
def create_workflow():
    planner_agent = Agent(
        client=create_chat_client(),
        name="ResolutionPlanner",
        instructions="You are a senior SAP Basis consultant producing concise incident resolution plans.",
    )
    planner_executor = AgentExecutor(planner_agent)

    parallel     = ParallelAnalysisExecutor()
    plan_router  = PlanRouter()
    approval     = ApprovalGateway()
    confirmation = ConfirmationExecutor()

    return (
        WorkflowBuilder(
            name="IncidentTriageWithApproval",
            start_executor=parallel,
            output_executors=[plan_router, approval, confirmation],
        )
        .add_edge(parallel, plan_router)
        .add_edge(plan_router, planner_executor)
        .add_edge(planner_executor, approval)
        .add_edge(approval, confirmation)
        .build()
    )

# DevUI launch

if __name__ == "__main__":
    workflow = create_workflow()

    print("=" * 60)
    print("Exercise 06 — DevUI: Parallel Analysis + HITL Approval")
    print("=" * 60)
    print()
    print("Workflow: IncidentTriageWithApproval")
    print("  Step 1 — Parallel : Classifier + Enricher (asyncio.gather)")
    print("  Step 2 — LLM      : Resolution Plan (ResolutionPlanner)")
    print("  Step 3 — HITL     : Human Approval  (type 'approve')")
    print("  Step 4 — Confirm  : 'Resolution plan started'")
    print()
    print("Open http://localhost:8080 in your browser.")
    print("Press Ctrl+C to stop.\n")

    serve(
        entities=[workflow],
        port=8080,
        auto_open=False,
    )
