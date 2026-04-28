# Exercise 03 — Basic Workflow: SAP Incident Triage Pipeline

## Goal
Build a de-terministic, multi-step workflow using `WorkflowBuilder` and
`Executor` nodes. The workflow automatically triages an incoming SAP incident:
classifies it, enriches it with system context, and drafts a resolution plan.

## Concepts covered
- `WorkflowBuilder` — assembles a DAG of steps
- `Executor` (class-based) — a processing node with state
- `@executor` (function-based) — a lightweight stateless step
- `@handler` — handles incoming messages
- `ctx.send_message()` — forwards data to the next node
- `ctx.yield_output()` — produces the final workflow result
- `Agent` inside a workflow — LLM reasoning as a workflow step

## Run
```bash
python exercises/ex03-basic-workflow/incident_triage_workflow.py
python exercises/ex03-basic-workflow/incident_triage_workflow.py -i
python exercises/ex03-basic-workflow/incident_triage_workflow.py -i -v
```

## Exercises
1. Run the workflow with the provided sample incident (non-interactive).
2. Run the workflow on an interactive way. First ask a random request (e.g. submit expenses) and then try again asking to create an incident.
   - Try these inputs when prompted:
     - `"I want to submit my expenses"` → should be declined
     - `"Something is broken in our SAP system"` → should trigger the triage workflow
     - `"I need to report an issue"` → should trigger the triage workflow
   - Open a ticket for the SBX environment. Make up all other values - see example below (not all fields are necessary)
3. Change the input to a performance incident on PRD and observe how the enrichment and resolution plan change.
   - Suggested short text: `"PRD: High CPU causing slow response times in FI postings"`
   - Suggested system ID: `PRD`
4. Add a fourth executor `NotificationDispatcher` that would send the plan to a mock email address (print to console) after the agent step.
5. Visualise the workflow - use the following as reference: https://learn.microsoft.com/en-us/agent-framework/workflows/visualization?pivots=programming-language-python

## Key takeaways
- Workflows are **deterministic** DAGs; agents add **reasoning** nodes.
- Mixing `Executor` and `Agent` nodes gives you controlled + intelligent steps.
- Each executor only knows about its neighbours — loose coupling by design.

## Prompt examples:
- incident_id="INC-2026-00314"
- system_id="SBX"
- short_text="SBX: Dialog work processes exhausted after transport import",
- long_text= After importing transport request DEVK912345 into SBX at 07:15 UTC, all dialog work processes on the application server APP01 became occupied. SM50 shows all WP in 'Running' state with the report ZFIN_BALANCE_CHECK. Users receive 'No more dialog work processes available' (error message M8 800). The system has not recovered on its own. Restarting the application server temporarily freed the work processes but the report started again within 5 minutes. The transport contains changes to Program ZFIN_BALANCE_CHECK (change request type: Workbench). System is a sandbox so business impact is low but this pattern must not reach QAS or PRD.
- reported_by="basis-team@contoso.com"
