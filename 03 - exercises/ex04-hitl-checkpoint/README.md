# Exercise 04 — HITL + Checkpoints: SAP Change Request Approval Workflow

## Goal
Build a workflow that pauses execution at a **human approval gate**, saves its
state as a **checkpoint**, and can be fully **resumed** after a restart,
even if the approver is not available immediately.

## Why this matters for SAP
Change Management activities require human sign-off on transports before they are imported into Production. This workflow models:

1. **Change Request Preparer** - formats the transport details for review
2. **AI Impact Analyser** - drafts a risk assessment using an agent
3. **Human Approval Gate** - pauses; waits for the change manager to approve
4. **Import Executor** - simulates import once approved

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
python exercises/ex04-hitl-checkpoint/change_request_workflow.py -i
```

The first run will:
1. Process the change request
2. Display the AI risk assessment
3. Pause and prompt you: **"Type 'approve' or enter rejection reason"**
4. After you respond, continue or loop back for revision
5. List available checkpoints and offer to resume from one

## Exercises
1. Run and type `exit`. Observe that a checkpoint has been created.
2. Re-run, observe that the agent identifies thar there is a checkpoint in place, and gives the user the option to resume without re-assessing the risk. Type `0` and then `approve` the workflow.
3. Run again and type a rejection reason (e.g. "missing downtime notification").
   Watch the agent revise the request.
4. Inspect the generated `.json` checkpoint files in `checkpoints/` to understand
   the persisted state format.

## Key takeaways
- `request_info` is the correct primitive for "pause and ask a human".
- Checkpoints make long-running approvals **crash-safe and resumable**.
- The pattern maps directly to SAP CHARM's "change document" approval flow.
