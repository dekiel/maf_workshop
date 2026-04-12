# Exercise 04 — HITL + Checkpoints: SAP Change Request Approval Workflow

## Goal
Build a workflow that pauses execution at a **human approval gate**, saves its
state as a **checkpoint**, and can be fully **resumed** after a restart —
even if the approver is not available immediately.

## Why this matters for SAP
SAP Change Management (CHARM, ChaRM, or ITSM) requires human sign-off on
transports before they are imported into Production. This workflow models:

1. **Change Request Preparer** — formats the transport details for review
2. **AI Impact Analyser** — drafts a risk assessment using an agent
3. **Human Approval Gate** — pauses; waits for the change manager to approve
4. **Import Executor** — simulates import once approved

## Concepts covered
- `ctx.request_info()` — emit a structured pause-and-respond request
- `@response_handler` — handle the human's reply after resume
- `FileCheckpointStorage` — persist workflow state to disk as JSON
- `on_checkpoint_save()` / `on_checkpoint_restore()` — custom state hooks
- `workflow.run(checkpoint_id=...)` — resume from a saved checkpoint
- `stream=True` on workflows — observe individual step events

## Run
```bash
python exercises/ex04-hitl-checkpoint/change_request_workflow.py
```

The first run will:
1. Process the change request
2. Display the AI risk assessment
3. Pause and prompt you: **"Type 'approve' or enter rejection reason"**
4. After you respond, continue or loop back for revision
5. List available checkpoints and offer to resume from one

## Expected output
```
=== SAP Change Request Approval Workflow ===

Processing change request: CRQ-2026-00042
Step 1 — Preparing change request details ...
Step 2 — AI analysing risk ...

=== Change Manager Approval Required ===
Change Request : CRQ-2026-00042
Transport      : DEVK912345  (PRD import)
Risk Assessment: [AI-generated text]

Type 'approve' to proceed or enter revision guidance (or 'exit'): approve

Change request CRQ-2026-00042 APPROVED. Proceeding to import simulation.
Workflow completed: Transport DEVK912345 import to PRD scheduled for next maintenance window.
```

## Exercises
1. Run and type `approve`. Observe the full approval path.
2. Run again and type a rejection reason (e.g. "missing downtime notification").
   Watch the agent revise the request.
3. Exit mid-run (`exit`). Restart the script and resume from the checkpoint.
4. Inspect the generated `.json` checkpoint files in `checkpoints/` to understand
   the persisted state format.

## Key takeaways
- `request_info` is the correct primitive for "pause and ask a human".
- Checkpoints make long-running approvals **crash-safe and resumable**.
- The pattern maps directly to SAP CHARM's "change document" approval flow.
