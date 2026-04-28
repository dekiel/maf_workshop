# Exercise 01 - Basic Agent: System Health Checker

## Goal
Create your first Microsoft Agent Framework agent. The agent exposes three
`@tool` functions that simulate IT operations: checking the status of a
system, listing open support messages and creating a support message.

## Concepts covered
- `Agent` — the core orchestration object
- `FoundryChatClient` — lightweight Azure AI Foundry chat client - this is optional, other clients can be used (see https://learn.microsoft.com/en-us/agent-framework/agents/providers/?pivots=programming-language-python)
- `@tool` decorator — turning a Python function into an AI-callable tool
- The approval_mode="never_require" is for workshop brevity. In production, use "always_require" for any tool that reads sensitive data or has side effects.
- Non-streaming and streaming responses
- Interactive and non-interactive responses (run the script with -i)
- Verbose mode to print which function is being called (run the script with -v)

## Prerequisites
- `.env` configured with `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL`
- `az login` completed

## Run
```bash
python "03 - exercises/ex01-basic-agent/sap_health_agent.py"
python "03 - exercises/ex01-basic-agent/sap_health_agent.py" --interactive
python "03 - exercises/ex01-basic-agent/sap_health_agent.py" --interactive --verbose
```

## Exercises
1. Run the file as-is and observe the output (non-interactive).
2. Run an interactive session and chat with the agent (-i).
3. Run an interactive session printing which tools are being called by the agent (-i -v).
4. (Optional) Change the `instructions` string to be more formal (e.g., "You are a senior IT engineer...") and re-run. Observe the changes.
5. (Optional) Change `approval_mode` on `create_support_message` from `"never_require"` to `"always_require"` — the agent will pause before executing the tool and emit an approval-request event instead of a text response. In a production app you would handle that event to show a confirmation UI before proceeding.
6. (Optional) Add a fourth tool `get_system_logs(system_id)` that returns mock application error logs and observe how the agent uses it automatically.

## Key takeaways
- `@tool` converts any Python function into a callable tool for the LLM.
- `approval_mode="always_require"` is the production default — use it for any
  tool with side effects.
- Streaming (`stream=True`) allows you to display tokens progressively.

## Prompt examples

Try these in `--interactive` mode to exercise all three tools:

1. `What is the current status of the PRD system?` — triggers **get_system_status**
2. `Show me all open P2 incidents across the entire landscape.` — triggers **list_open_incidents**
3. `Is QAS healthy? I need to know CPU and memory before the regression test.` — triggers **get_system_status** (with reasoning)
4. `List all P1 incidents on the SBX system.` — triggers **list_open_incidents** with a system filter
5. `The SBX system is down — please open a P1 support message with the subject "SBX: Application server down after maintenance window".` — triggers **create_support_message**

