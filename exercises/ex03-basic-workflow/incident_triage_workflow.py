"""
Exercise 03 — Basic Workflow: SAP Incident Triage Pipeline

This workflow automatically processes an incoming SAP support incident through the following stages:

  Step 0 (Agent)
      An intent-classification agent determines if the user wants to open an incident. (only for interactive method)
      If yes, the workflow continues to the next steps. Otherwise, it yields a polite decline
  Step 1 — IncidentClassifier (Executor)
      Reads the raw incident text and maps it to a SAP component category,
      priority level, and responsible team.
  Step 2 — SystemEnricher (Executor)
      Looks up the affected system's current health to add live context.
  Step 3 — ResolutionPlanner (Agent)
      Uses an LLM to draft a resolution plan based on the classified +
      enriched incident data.
  Step 4 — OutputCollector (@executor)
      Captures the final plan and yields it as the workflow output.

References
----------
- Workflow samples: https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows
- First workflow tutorial: python/samples/01-get-started/05_first_workflow.py
"""

import asyncio
import functools
import json
import os
from dataclasses import dataclass

from agent_framework import (
    Agent,
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    executor,
    handler,
)
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
from typing_extensions import Never

load_dotenv()

# Set to True via --verbose / -v at startup (see __main__)
VERBOSE: bool = False


def _verbose(label: str, data: object) -> None:
    """Print a step label and its data when VERBOSE=True."""
    if VERBOSE:
        print(f"\n[verbose] {label}: {json.dumps(data, default=str, indent=2)}", flush=True)


# Data model
@dataclass
class SAPIncident:
    """Represents a raw incoming SAP support incident."""
    incident_id: str
    system_id: str
    short_text: str
    long_text: str
    reported_by: str


@dataclass
class ClassifiedIncident:
    """Enriched incident after classification."""
    incident: SAPIncident
    sap_component: str 
    incident_category: str   
    responsible_team: str
    suggested_priority: str


@dataclass
class EnrichedIncident:
    """Classified incident combined with live system context."""
    classified: ClassifiedIncident
    system_status: str
    system_cpu_pct: int
    system_mem_pct: int


@dataclass
class UserRequest:
    """Bundles the user's intent message with the pre-filled incident data."""
    user_message: str
    incident: SAPIncident

# Step 0 (class-based Executor)
class RouterExecutor(Executor):
    """
    Step 0: Classify the user's intent.
    If the user wants to open an incident, route to the triage pipeline.
    Otherwise, yield a polite decline as the workflow output.
    """

    def __init__(self, agent: Agent) -> None:
        super().__init__(id="router")
        self._agent = agent

    @handler
    async def route(
        self,
        request: UserRequest,
        ctx: WorkflowContext[SAPIncident, str],
    ) -> None:
        result = await self._agent.run(request.user_message)
        if result.text.strip().upper().startswith("YES"):
            print("  Step 0 — Router: intent=OPEN_INCIDENT → routing to triage pipeline")
            _verbose("Router", {"intent": "OPEN_INCIDENT", "user_message": request.user_message})
            await ctx.send_message(request.incident)
        else:
            print("  Step 0 \u2014 Router: intent=OTHER \u2192 declining")
            _verbose("Router", {"intent": "OTHER", "response": result.text})
            await ctx.yield_output(result.text)


# Step 1 (class-based Executor)
# Simple keyword-based SAP component mapper.
_COMPONENT_MAP = {
    "work process": ("BC-SYS", "System Down", "SAP Basis"),
    "transport": ("BC-CTS", "Transport", "SAP Basis"),
    "authoris": ("BC-SEC", "Authorisation", "Security Team"),
    "authorization": ("BC-SEC", "Authorisation", "Security Team"),
    "cpu": ("BC-OP-NT", "Performance", "SAP Basis"),
    "performance": ("BC-OP-NT", "Performance", "SAP Basis"),
    "memory": ("BC-OP-NT", "Performance", "SAP Basis"),
    "billing": ("SD-BIL", "Finance & SD", "SD/FI Team"),
    "payment": ("FI-FBL", "Finance", "FI Team"),
    "fiori": ("EP-PIN-FRW", "Fiori / UI5", "UX Team"),
    "odata": ("BC-ESI-WS", "OData / API", "Integration Team"),
    "rfc": ("BC-MID-RFC", "RFC / Middleware", "Integration Team"),
}

class IncidentClassifier(Executor):
    """
    Step 1: Classify an incoming SAP incident into SAP component, category,
    and responsible team based on keyword matching.
    """

    def __init__(self) -> None:
        super().__init__(id="incident_classifier")

    @handler
    async def classify(
        self,
        incident: SAPIncident,
        ctx: WorkflowContext[ClassifiedIncident],
    ) -> None:
        combined_text = (incident.short_text + " " + incident.long_text).lower()

        sap_component, category, team = "BC-GEN", "General", "SAP Basis"
        for keyword, mapping in _COMPONENT_MAP.items():
            if keyword in combined_text:
                sap_component, category, team = mapping
                break

        priority = "P1" if "down" in combined_text or "cannot" in combined_text else "P2"

        classified = ClassifiedIncident(
            incident=incident,
            sap_component=sap_component,
            incident_category=category,
            responsible_team=team,
            suggested_priority=priority,
        )

        print(
            f"  Step 1 — Classifier: "
            f"Component={classified.sap_component} | "
            f"Category={classified.incident_category} | "
            f"Priority={classified.suggested_priority}"
        )
        _verbose("ClassifiedIncident", {
            "sap_component": classified.sap_component,
            "incident_category": classified.incident_category,
            "responsible_team": classified.responsible_team,
            "suggested_priority": classified.suggested_priority,
        })

        await ctx.send_message(classified)


# Step 2 — SystemEnricher (class-based Executor)
_SYSTEM_STATUS_DB = {
    "PRD": {"status": "GREEN", "cpu_pct": 42, "mem_pct": 67},
    "QAS": {"status": "YELLOW", "cpu_pct": 78, "mem_pct": 82},
    "DEV": {"status": "GREEN", "cpu_pct": 15, "mem_pct": 44},
    "SBX": {"status": "RED", "cpu_pct": 95, "mem_pct": 91},
}

class SystemEnricher(Executor):
    """
    Step 2: Look up live system health metrics and attach them to the incident.
    In production this would query SAP CCMS, Azure Monitor, or Solution Manager.
    """

    def __init__(self) -> None:
        super().__init__(id="system_enricher")

    @handler
    async def enrich(
        self,
        classified: ClassifiedIncident,
        ctx: WorkflowContext[AgentExecutorRequest],
    ) -> None:
        sid = classified.incident.system_id.upper()
        metrics = _SYSTEM_STATUS_DB.get(sid, {"status": "UNKNOWN", "cpu_pct": 0, "mem_pct": 0})

        enriched = EnrichedIncident(
            classified=classified,
            system_status=metrics["status"],
            system_cpu_pct=metrics["cpu_pct"],
            system_mem_pct=metrics["mem_pct"],
        )

        print(
            f"  Step 2 — Enrichment: "
            f"{sid} status={enriched.system_status}, "
            f"CPU={enriched.system_cpu_pct}%, "
            f"MEM={enriched.system_mem_pct}%"
        )
        _verbose("EnrichedIncident", {
            "system_id": sid,
            "status": enriched.system_status,
            "cpu_pct": enriched.system_cpu_pct,
            "mem_pct": enriched.system_mem_pct,
        })

        # Build a structured prompt for the downstream agent
        prompt = (
            f"You are an SAP Basis expert. Prepare a concise resolution plan "
            f"(max 200 words) for the following incident.\n\n"
            f"Incident ID    : {classified.incident.incident_id}\n"
            f"System         : {sid} — currently {enriched.system_status} "
            f"(CPU {enriched.system_cpu_pct}%, MEM {enriched.system_mem_pct}%)\n"
            f"SAP Component  : {classified.sap_component}\n"
            f"Category       : {classified.incident_category}\n"
            f"Priority       : {classified.suggested_priority}\n"
            f"Responsible    : {classified.responsible_team}\n\n"
            f"Problem description:\n{classified.incident.short_text}\n\n"
            f"{classified.incident.long_text}\n\n"
            f"Produce:\n"
            f"1. Root cause hypothesis\n"
            f"2. Immediate containment steps\n"
            f"3. Long-term fix recommendation\n"
        )

        await ctx.send_message(
            AgentExecutorRequest(
                messages=[Message("user", contents=[prompt])],
                should_respond=True,
            )
        )

# Step 3 — OutputCollector (function-based @executor)
@executor(id="output_collector")
async def output_collector(
    response: AgentExecutorResponse,
    ctx: WorkflowContext[Never, str],
) -> None:
    """Collect the agent's resolution plan and publish it as workflow output."""
    print("  Step 3 — Output collected.")
    await ctx.yield_output(response.agent_response.text)


# Workflow assembly
def create_triage_workflow():
    # Step 0: Intent router
    router_agent = Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        ),
        name="IncidentRouter",
        instructions=(
            "You are an intent classifier for an SAP Support Desk. "
            "Decide whether the user wants to open, report, or create a support incident or ticket. "
            "This includes any variation such as 'I have a problem', 'something is broken', "
            "'I need to report an issue', 'open a ticket', 'create an incident', etc. "
            "If yes, reply with exactly: YES\n"
            "If the user is asking something unrelated (e.g. system status, general questions, greetings), "
            "reply with a short, polite message explaining you can only help with opening SAP support incidents."
        ),
    )
    router = RouterExecutor(router_agent)

    # Step 3: LLM-powered resolution planner
    planner_agent = Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        ),
        name="ResolutionPlanner",
        instructions="You are a senior SAP Basis consultant producing concise incident resolution plans.",
    )
    planner_executor = AgentExecutor(planner_agent)

    classifier = IncidentClassifier()
    enricher = SystemEnricher()

    workflow = (
        WorkflowBuilder(start_executor=router, output_executors=[router, output_collector])
        .add_edge(router, classifier)
        .add_edge(classifier, enricher)
        .add_edge(enricher, planner_executor)
        .add_edge(planner_executor, output_collector)
        .build()
    )
    return workflow


# Main

_SAMPLE_INCIDENT = SAPIncident(
    incident_id="INC-2026-00314",
    system_id="SBX",
    short_text="SBX: Dialog work processes exhausted after transport import",
    long_text=(
        "After importing transport request DEVK912345 into SBX at 07:15 UTC, "
        "all dialog work processes on the application server APP01 became occupied. "
        "SM50 shows all WP in 'Running' state with the report ZFIN_BALANCE_CHECK. "
        "Users receive 'No more dialog work processes available' (error message M8 800). "
        "The system has not recovered on its own. Restarting the application server "
        "temporarily freed the work processes but the report started again within 5 minutes. "
        "The transport contains changes to Program ZFIN_BALANCE_CHECK (change request type: "
        "Workbench). System is a sandbox so business impact is low but this pattern must "
        "not reach QAS or PRD."
    ),
    reported_by="basis-team@contoso.com",
)


async def _run_incident(request: UserRequest) -> None:
    print("SAP Support Desk Workflow")
    print(f"\nProcessing incident : {request.incident.incident_id}")
    print(f"System              : {request.incident.system_id}")
    print(f"Short text          : {request.incident.short_text}\n")

    workflow = create_triage_workflow()
    events = await workflow.run(request)  # Non-streaming execution — wait for completion (see https://learn.microsoft.com/en-us/agent-framework/workflows/workflows?pivots=programming-language-python)

    outputs = events.get_outputs()
    if outputs:
        print(f"\n{outputs[0]}")
    else:
        print("No output produced.")


async def main() -> None:
    await _run_incident(UserRequest(
        user_message="I need to open a support incident",
        incident=_SAMPLE_INCIDENT,
    ))


async def interactive() -> None:
    """Ask what the user needs, route intent, then collect incident details only if needed."""
    print("SAP Support Desk\n")
    print("Hello! I'm the SAP Support Desk assistant. I can help you open SAP support incidents.\n")

    user_msg = input("What do you need help with today?\nYou: ").strip()
    if not user_msg:
        print("No input received. Goodbye!")
        return

    # Check intent directly via the router agent, before asking for any details
    router_agent = Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ["FOUNDRY_MODEL"],
            credential=AzureCliCredential(),
        ),
        name="IncidentRouter",
        instructions=(
            "You are an intent classifier for an SAP Support Desk. "
            "Decide whether the user wants to open, report, or create a support incident or ticket. "
            "This includes any variation such as 'I have a problem', 'something is broken', "
            "'I need to report an issue', 'open a ticket', 'create an incident', etc. "
            "If yes, reply with exactly: YES\n"
            "If the user is asking something unrelated (e.g. system status, general questions, greetings), "
            "reply with a short, polite message explaining you can only help with opening SAP support incidents."
        ),
    )
    intent_result = await router_agent.run(user_msg)
    if not intent_result.text.strip().upper().startswith("YES"):
        print(f"\nAgent: {intent_result.text}\n")
        return

    # --- Intent confirmed — now collect the real incident details from the user ---
    print("\nSure! Please fill in the incident details (press Enter to accept the default):\n")

    incident_id = input(f"Incident ID [{_SAMPLE_INCIDENT.incident_id}]: ").strip() or _SAMPLE_INCIDENT.incident_id
    system_id   = input(f"System ID (PRD/QAS/DEV/SBX) [{_SAMPLE_INCIDENT.system_id}]: ").strip() or _SAMPLE_INCIDENT.system_id
    short_text  = input(f"Short text [{_SAMPLE_INCIDENT.short_text}]: ").strip() or _SAMPLE_INCIDENT.short_text
    long_text   = input("Long text (or Enter to use default): ").strip() or _SAMPLE_INCIDENT.long_text
    reported_by = input(f"Reported by [{_SAMPLE_INCIDENT.reported_by}]: ").strip() or _SAMPLE_INCIDENT.reported_by

    incident = SAPIncident(
        incident_id=incident_id,
        system_id=system_id,
        short_text=short_text,
        long_text=long_text,
        reported_by=reported_by,
    )
    print()
    await _run_incident(UserRequest(user_message=user_msg, incident=incident))


if __name__ == "__main__":
    import sys
    if "--verbose" in sys.argv or "-v" in sys.argv:
        VERBOSE = True
        print("[verbose mode ON — step data will be printed]\n")
    if "--interactive" in sys.argv or "-i" in sys.argv:
        asyncio.run(interactive())
    else:
        asyncio.run(main())
