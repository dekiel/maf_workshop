"""
Exercise 04 — HITL + Checkpoints: Change Request Approval Workflow

This workflow models the Change Request approval cycle:

  1. ChangeRequestPreparer (Executor)
       Formats the transport details into a structured review package.

  2. RiskAnalyser (AgentExecutor)
       Uses an LLM to assess the risk level and potential impact of the transport.

  3. ApprovalGateway (Executor)
       Emits a human-in-the-loop request and waits.
       The workflow checkpoints here so the program can be stopped and resumed.

  4. ImportSimulator (@executor)
       Simulates the transport import if the change is approved.
       Loops back to the RiskAnalyser if the change manager requests revisions.

References
----------
- Checkpoint sample: https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/checkpoint/checkpoint_with_human_in_the_loop.py
- HITL sample: https://github.com/microsoft/agent-framework/blob/main/python/samples/03-workflows/human-in-the-loop/agents_with_approval_requests.py
"""

import asyncio
import functools
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework import (
    Agent,
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    FileCheckpointStorage,
    Message,
    Workflow,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)
from dotenv import load_dotenv
from shared.model_client import create_chat_client

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override  # type: ignore[import]

load_dotenv()

# Set to True via --verbose / -v at startup (see __main__)
VERBOSE: bool = False


def _create_agent(name: str, instructions: str, tools: list | None = None) -> Agent:
    """Create an Agent with the configured LLM client."""
    return Agent(
        client=create_chat_client(),
        name=name,
        instructions=instructions,
        tools=tools or [],
    )


def _verbose(label: str, data: object) -> None:
    """Print step data when VERBOSE=True."""
    if VERBOSE:
        print(f"\n[verbose] {label}: {json.dumps(data, default=str, indent=2)}", flush=True)


CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"

# Data models
@dataclass
class ChangeRequest:
    """SAP Change Request (transport) submitted for approval."""
    crq_id: str
    transport_id: str
    source_system: str
    target_system: str
    description: str
    developer: str
    objects_changed: list[str]


@dataclass
class ReviewPackage:
    """Prepared change request enriched for the approver."""

    crq: ChangeRequest
    risk_assessment: str = ""
    iteration: int = 0


@dataclass
class ApprovalRequest:
    """Structured pause request sent to the human change manager."""
    prompt: str
    crq_id: str
    transport_id: str
    target_system: str
    risk_assessment: str
    iteration: int


# Step 1 — ChangeRequestPreparer
class ChangeRequestPreparer(Executor):
    """Format the incoming change request into a structured review package."""

    def __init__(self) -> None:
        super().__init__(id="change_request_preparer")

    @handler
    async def prepare(
        self,
        crq: ChangeRequest,
        ctx: WorkflowContext[AgentExecutorRequest],
    ) -> None:
        print(f"\n  Step 1 — Formatting the change request for the AI ...")
        print(f"          (Transport {crq.transport_id}: {crq.source_system} -> {crq.target_system})")
        _verbose("ChangeRequest", {
            "crq_id": crq.crq_id,
            "transport": crq.transport_id,
            "path": f"{crq.source_system} -> {crq.target_system}",
            "objects": crq.objects_changed,
        })

        # Build a prompt for the AI risk analyser
        objects_list = "\n".join(f"    - {obj}" for obj in crq.objects_changed)
        prompt = (
            f"You are an SAP change management expert. "
            f"Produce a concise risk assessment (max 150 words) for this transport:\n\n"
            f"Change Request  : {crq.crq_id}\n"
            f"Transport       : {crq.transport_id}\n"
            f"Path            : {crq.source_system} -> {crq.target_system}\n"
            f"Developer       : {crq.developer}\n"
            f"Description     : {crq.description}\n\n"
            f"Objects changed:\n{objects_list}\n\n"
            f"Include:\n"
            f"  1. Risk level (Low / Medium / High / Critical)\n"
            f"  2. Potential business impact\n"
            f"  3. Recommended pre-import checks\n"
            f"  4. Rollback strategy\n"
        )

        ctx.set_state("crq", crq)
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[Message("user", contents=[prompt])],
                should_respond=True,
            )
        )

# Step 3 — ApprovalGateway (HITL + checkpoint)
class ApprovalGateway(Executor):
    """
    Emit a human approval request and wait.
    Supports checkpoint save/restore so the program can be stopped and resumed.
    """

    def __init__(self, crq_id: str) -> None:
        super().__init__(id="approval_gateway")
        self._crq_id = crq_id
        self._iteration = 0

    @handler
    async def on_risk_assessment(
        self,
        response: AgentExecutorResponse,
        ctx: WorkflowContext,
    ) -> None:
        self._iteration += 1
        crq: ChangeRequest = ctx.get_state("crq")

        print(f"\n  Step 3: Saving checkpoint to disk (workflow state is now persisted)")
        print(f"Pausing for human approval - this is the HITL moment.")
        print(f"The workflow will wait here until a person responds.")

        await ctx.request_info(
            request_data=ApprovalRequest(
                prompt=(
                    "Review the risk assessment below. "
                    "Type 'approve' to proceed or provide revision guidance."
                ),
                crq_id=crq.crq_id,
                transport_id=crq.transport_id,
                target_system=crq.target_system,
                risk_assessment=response.agent_response.text,
                iteration=self._iteration,
            ),
            response_type=str,
        )

    @response_handler
    async def on_approval_response(
        self,
        original_request: ApprovalRequest,
        feedback: str,
        ctx: WorkflowContext[AgentExecutorRequest | str, str],
    ) -> None:
        reply = feedback.strip()
        if not reply or reply.lower() == "approve":
            print(f"\n Change request {original_request.crq_id} APPROVED.")
            import_message = (
                f"Transport {original_request.transport_id} import to "
                f"{original_request.target_system} scheduled for next maintenance window."
            )
            await ctx.yield_output(import_message)
            return

        # Revision requested — loop back to the risk analyser
        print(f"\n Revision requested: {reply}")
        crq: ChangeRequest = ctx.get_state("crq")
        revision_prompt = (
            f"Revise the risk assessment based on the change manager's feedback.\n\n"
            f"Previous assessment:\n{original_request.risk_assessment}\n\n"
            f"Change manager feedback: {reply}\n\n"
            f"Provide a revised assessment for transport {crq.transport_id}."
        )
        await ctx.send_message(
            AgentExecutorRequest(
                messages=[Message("user", contents=[revision_prompt])],
                should_respond=True,
            )
        )

    @override
    async def on_checkpoint_save(self) -> dict[str, Any]:
        return {"iteration": self._iteration, "crq_id": self._crq_id}

    @override
    async def on_checkpoint_restore(self, state: dict[str, Any]) -> None:
        self._iteration = state.get("iteration", 0)
        self._crq_id = state.get("crq_id", self._crq_id)


# Workflow assembly
def create_workflow(crq: ChangeRequest, storage: FileCheckpointStorage) -> Workflow:
    risk_agent = _create_agent(
        name="RiskAnalyser",
        instructions=(
            "You are a senior SAP change management consultant. "
            "Write precise, actionable risk assessments for SAP transport imports."
        ),
    )
    risk_executor = AgentExecutor(risk_agent)

    preparer = ChangeRequestPreparer()
    gateway = ApprovalGateway(crq_id=crq.crq_id)

    return (
        WorkflowBuilder(
            name="change_request_approval",
            max_iterations=10,
            start_executor=preparer,
            checkpoint_storage=storage,
        )
        .add_edge(preparer, risk_executor)
        .add_edge(risk_executor, gateway)
        .add_edge(gateway, risk_executor)   # revision loop
        .build()
    )
# Interactive session helper
def prompt_for_approval(requests: dict[str, ApprovalRequest]) -> dict[str, str]:
    responses: dict[str, str] = {}
    for request_id, req in requests.items():
        print("\n" + "=" * 60)
        print("=== SAP Change Management — Approval Required ===")
        print("=" * 60)
        print(f"Change Request : {req.crq_id}")
        print(f"Transport      : {req.transport_id}  ->  {req.target_system}")
        print(f"Iteration      : {req.iteration}")
        print(f"\n{req.prompt}")
        print(f"\nRisk Assessment:\n---\n{req.risk_assessment}\n---")
        response = input("\nType 'approve' or enter revision guidance (or 'exit' to quit): ").strip()
        if response.lower() == "exit":
            raise SystemExit("Stopped by user.")
        responses[request_id] = response
    return responses


async def _drain_stream(
    event_stream,
) -> tuple[dict[str, ApprovalRequest], str | None]:
    """Drain one workflow stream pass.

    Returns:
        (requests, output) where *requests* maps request_id → ApprovalRequest
        for any pending HITL pauses, and *output* is the final workflow output
        produced by ``ctx.yield_output`` (None if the workflow paused for input).
    """
    requests: dict[str, ApprovalRequest] = {}
    output: str | None = None
    async for event in event_stream:
        if event.type == "request_info":
            requests[event.request_id] = event.data
        elif event.type == "output" and event.data and not requests:
            # Only capture non-token output (yield_output) and only when no
            # HITL pause has been signalled yet — streaming tokens arrive
            # before any request_info event, so once we see a request we stop
            # overwriting output with tokens.
            output = event.data
    return requests, output


async def run_workflow(
    workflow: Workflow,
    crq: ChangeRequest | None = None,
    checkpoint_id: str | None = None,
) -> str:
    """Run (or resume) the workflow, handling HITL requests interactively.
    Follows the pattern from the official docs:
    https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop
    """
    if checkpoint_id:
        print("\nResuming from checkpoint ...\n")
        stream = workflow.run(checkpoint_id=checkpoint_id, stream=True)
    else:
        stream = workflow.run(message=crq, stream=True)

    requests, output = await _drain_stream(stream)

    while requests:
        responses = prompt_for_approval(requests)
        stream = workflow.run(stream=True, responses=responses)
        requests, output = await _drain_stream(stream)

    return output or ""


# Main
_SAMPLE_CRQ = ChangeRequest(
    crq_id="CRQ-2026-00042",
    transport_id="DEVK912345",
    source_system="DEV",
    target_system="PRD",
    description=(
        "Extend SD billing output condition table (KOTN500) with new pricing logic "
        "for RISE with SAP cloud customers. Adds two new condition types ZSC1 and ZSC2 "
        "to accommodate subscription-based billing scenarios."
    ),
    developer="d.mueller@contoso.com",
    objects_changed=[
        "Table: KOTN500 (new fields: ZCOND_RISE, ZBILLING_MODEL)",
        "Program: RV60AFZZ (billing user exit — condition type mapping)",
        "Customizing: Pricing procedure ZRVAAA01 (new steps 910, 920)",
        "Function Group: V60A (FORM routine Z_RISE_CONDITION_VALUE)",
    ],
)

async def main() -> None:
    CHECKPOINT_DIR.mkdir(exist_ok=True)

    sample_crq = _SAMPLE_CRQ
    storage = FileCheckpointStorage(
        storage_path=CHECKPOINT_DIR,
        allowed_checkpoint_types={
            f"{ChangeRequest.__module__}:{ChangeRequest.__qualname__}",
            f"{ReviewPackage.__module__}:{ReviewPackage.__qualname__}",
            f"{ApprovalRequest.__module__}:{ApprovalRequest.__qualname__}",
        },
    )
    workflow = create_workflow(sample_crq, storage)

    # If a checkpoint exists from a previous run, offer to resume it
    checkpoints = await storage.list_checkpoints(workflow_name=workflow.name)
    if checkpoints:
        sorted_cps = sorted(checkpoints, key=lambda cp: datetime.fromisoformat(cp.timestamp))
        print("=== Exercise 04 — Human-in-the-Loop + Checkpoints ===")
        print(f"\n💾 Found {len(sorted_cps)} saved checkpoint(s) from a previous run.")
        print("   This is what makes checkpoints useful: the workflow can resume")
        print("   even after the program stopped, crashed, or went offline.\n")
        for idx, cp in enumerate(sorted_cps):
            print(f"  [{idx}] saved at {cp.timestamp[:19]}  (after {cp.iteration_count} step(s))")
        choice = input("\nResume from a checkpoint? Enter number, or press Enter to start fresh: ").strip()
        if choice.isdigit():
            chosen = sorted_cps[min(int(choice), len(sorted_cps) - 1)]
            print(f"\n▶ Resuming from checkpoint {chosen.checkpoint_id[:8]}...")
            result = await run_workflow(workflow, checkpoint_id=chosen.checkpoint_id)
            print(f"\nWorkflow completed: {result}")
            return
        else:
            for f in CHECKPOINT_DIR.glob("*.json"):
                f.unlink()
            workflow = create_workflow(sample_crq, storage)

    print("=== Exercise 04 — Human-in-the-Loop + Checkpoints ===")
    print()
    print("What you will see:")
    print("  1. The AI analyses the transport risk and writes a report.")
    print("  2. The workflow PAUSES and asks you to approve.")
    print("     ➜ A checkpoint is saved to disk at this moment.")
    print("  3. Type 'exit' to simulate going offline or closing the terminal.")
    print("  4. Run the script again — it will find the checkpoint and offer to resume.")
    print()
    print(f"Transport {sample_crq.transport_id}: {sample_crq.source_system} -> {sample_crq.target_system}")
    print()

    result = await run_workflow(workflow, crq=sample_crq)
    if result:
        print(f"\nWorkflow completed: {result}")
        # Clean up after a successful full run
        for f in CHECKPOINT_DIR.glob("*.json"):
            f.unlink()


async def interactive() -> None:
    """Prompt the user for a change request and run the approval workflow."""
    print("SAP Change Request Approval — Interactive Mode")
    print("Press Enter to keep the default value shown in brackets.\n")

    _d = _SAMPLE_CRQ
    print("A transport is a packaged set of code or config changes moved between SAP systems (DEV -> QAS -> PRD).\n")
    transport   = input(f"Transport ID (e.g. DEVK912345 or QASK900012) [{_d.transport_id}]: ").strip() or _d.transport_id
    target      = input(f"Target system — where to import it (DEV / QAS / PRD) [{_d.target_system}]: ").strip() or _d.target_system
    description = input(f"What does this change do? [{_d.description[:60]}...]: ").strip() or _d.description

    crq = ChangeRequest(
        crq_id=_d.crq_id,
        transport_id=transport,
        source_system=_d.source_system,
        target_system=target,
        description=description,
        developer=_d.developer,
        objects_changed=_d.objects_changed,
    )
    print()

    CHECKPOINT_DIR.mkdir(exist_ok=True)
    storage = FileCheckpointStorage(storage_path=CHECKPOINT_DIR)
    workflow = create_workflow(crq, storage)

    print(f"Change Request : {crq.crq_id}")
    print(f"Transport      : {crq.transport_id}  ({crq.source_system} -> {crq.target_system})\n")

    result = await run_workflow(workflow, crq=crq)
    print(f"\nWorkflow completed: {result}")


if __name__ == "__main__":
    if "--verbose" in sys.argv or "-v" in sys.argv:
        VERBOSE = True
        print("[verbose mode ON — step data will be printed]\n")
    if "--interactive" in sys.argv or "-i" in sys.argv:
        asyncio.run(interactive())
    else:
        asyncio.run(main())
