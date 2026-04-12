"""
Exercise 01 — Basic Agent: System Health Checker

This sample creates a minimal MAF agent that can answer questions about
a mock company landscape. The agent is equipped with three tools:

  - get_system_status()   — returns the health of a named system
  - list_open_incidents() — lists open support incidents
  - create_support_message() — opens a support message (side effect, requires approval)

Context
-----------
The IT operations team routinely monitor multiple systems (DEV, QAS, PRD, SBX).
Instead of logging into each system's GUI, this agent surfaces status in natural
language and can draft support messages on request.

References
----------
- Agent Framework docs: https://learn.microsoft.com/azure/developer/agent-framework/
- Samples: https://github.com/microsoft/agent-framework/tree/main/python/samples
"""

import asyncio
import functools
import json
import os
import random
from datetime import UTC, datetime
from typing import Annotated

from agent_framework import Agent, Message, tool
from agent_framework.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from pydantic import Field

# Azure AI Foundry client (alternative)
# from agent_framework.foundry import FoundryChatClient  
# from azure.identity import AzureCliCredential  

load_dotenv()

# Set to True via --verbose / -v at startup (see __main__)
VERBOSE: bool = False

def _verbose_tool(fn):
    """Wrap a tool function to print its call and return value when VERBOSE=True."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if VERBOSE:
            all_args = {**dict(zip(fn.__code__.co_varnames, args)), **kwargs}
            print(f"\n[tool call]  {fn.__name__}({json.dumps(all_args)})", flush=True)
        result = fn(*args, **kwargs)
        if VERBOSE:
            print(f"[tool result] {json.dumps(result, default=str)}", flush=True)
        return result
    return wrapper


@tool(approval_mode="never_require")
@_verbose_tool
def get_system_status(
    system_id: Annotated[
        str,
        Field(description="System ID, e.g. PRD, QAS, DEV, SBX"),
    ],
) -> dict:
    """
    Return the current health status of a named system.
    It uses simulated data.
    """

    systems = {
        "PRD": {"status": "GREEN", "cpu_pct": 42, "mem_pct": 67, "active_wp": 1205},
        "QAS": {"status": "YELLOW", "cpu_pct": 78, "mem_pct": 82, "active_wp": 340},
        "DEV": {"status": "GREEN", "cpu_pct": 15, "mem_pct": 44, "active_wp": 88},
        "SBX": {"status": "RED", "cpu_pct": 95, "mem_pct": 91, "active_wp": 0},
    }
    sid = system_id.upper()
    if sid not in systems:
        return {"error": f"Unknown system: {system_id}. Known systems: {list(systems.keys())}"}
    info = systems[sid]
    return {
        "system_id": sid,
        **info,
        "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@tool(approval_mode="never_require")
@_verbose_tool
def list_open_incidents(
    priority: Annotated[
        str,
        Field(description="Priority: P1 (very high), P2 (high), P3 (medium), P4 (low)"),
    ] = "P1",
    system_id: Annotated[
        str | None,
        Field(description="Filter by system. Leave empty for all systems."),
    ] = None,
) -> list[dict]:
    """
    Return a list of open support incidents filtered by priority.
    It uses simulated data.
    """
    all_incidents = [
        {
            "id": "INC-2026-00314",
            "priority": "P1",
            "system": "SBX",
            "category": "System Down",
            "short_text": "SBX: Dialog work processes exhausted after transport import",
            "created_at": "2026-04-05T07:22:00Z",
        },
        {
            "id": "INC-2026-00309",
            "priority": "P2",
            "system": "QAS",
            "category": "Performance",
            "short_text": "QAS: High CPU on application server APP01 — suspected runaway report",
            "created_at": "2026-04-04T14:05:00Z",
        },
        {
            "id": "INC-2026-00298",
            "priority": "P2",
            "system": "PRD",
            "category": "Authorisation",
            "short_text": "PRD: Users in role ZSD_SALES cannot post billing documents (SU53 dump)",
            "created_at": "2026-04-03T09:48:00Z",
        },
        {
            "id": "INC-2026-00276",
            "priority": "P3",
            "system": "DEV",
            "category": "Basis",
            "short_text": "DEV: Background job REORG_ABAPDUMPS missed scheduled start",
            "created_at": "2026-04-02T16:30:00Z",
        },
    ]

    results = [i for i in all_incidents if i["priority"] == priority.upper()]
    if system_id:
        results = [i for i in results if i["system"] == system_id.upper()]
    return results


@tool(approval_mode="never_require")  # use "always_require" in production for side-effect tools
@_verbose_tool
def create_support_message(
    system_id: Annotated[str, Field(description="Affected System ID")],
    priority: Annotated[str, Field(description="P1, P2, P3, or P4")],
    short_text: Annotated[str, Field(description="Brief description of the problem")]
) -> dict:
    """
    Create a new support message (incident) in the ticketing system.
    This tool ALWAYS requires human approval because it has a production side effect.
    """
    # In a real implementation this would call the support API.
    ticket_id = f"INC-2026-{random.randint(400, 999):05d}"  # noqa: S311
    return {
        "ticket_id": ticket_id,
        "status": "OPEN",
        "system_id": system_id.upper(),
        "priority": priority,
        "short_text": short_text,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "message": f"Support message {ticket_id} created successfully.",
    }


def _create_agent() -> Agent:
    """Create the Health Agent with the configured LLM client."""
    ## GitHub Models client — set GITHUB_PAT and GITHUB_MODEL in your .env
    
    # Alternatively, use FoundryChatClient for Azure AI Foundry:
    # client = FoundryChatClient(
    #     project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    #     model=os.environ["FOUNDRY_MODEL"],
    #     credential=AzureCliCredential(),
    # )
    
    client = OpenAIChatCompletionClient(
        model=os.environ.get("GITHUB_MODEL", "gpt-4o"),
        api_key=os.environ["GITHUB_PAT"],
        base_url="https://models.inference.ai.azure.com",
    )
    return Agent(
        client=client,
        name="HealthAgent",
        instructions=(
            "You are a knowledgeable Basis assistant. "
            "You help the team monitor system health, review open incidents, "
            "and draft support messages. "
            "Always reference the system ID in your answers. "
            "Be concise and professional."
        ),
        tools=[get_system_status, list_open_incidents, create_support_message],
    )

# Main - for non interactive session
async def main() -> None:

    agent = _create_agent()

    print("System Health Agent \n")

    # --- Non-streaming: get the full answer at once ---
    question1 = "What is the current status of PRD and QAS systems?"
    print(f"[non-streaming]\nUser: {question1}")
    result = await agent.run(question1)
    print(f"Agent: {result.text}\n")

    # --- Streaming: receive tokens progressively ---
    question2 = "List all open P1 and P2 incidents across our landscape."
    print(f"[streaming]\nUser: {question2}")
    print("Agent (streaming): ", end="", flush=True)
    async for chunk in agent.run(question2, stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print("\n")

# Main - for interactive session
async def interactive() -> None:
    """Interactive terminal loop — type your own questions."""
    agent = _create_agent()

    print("System Health Agent — interactive mode")
    print("Type your question and press Enter. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # --- streaming loop with approval handling ---
        current_input: str | list = user_input
        pending_approvals = True

        while pending_approvals:
            pending_approvals = False
            collected_requests = []

            print("Agent: ", end="", flush=True)
            # Stream the response
            async for chunk in agent.run(current_input, stream=True):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                # Collect user input requests from the stream
                if chunk.user_input_requests:
                    collected_requests.extend(chunk.user_input_requests)
            print()

            if collected_requests:
                pending_approvals = True
                # Start with the original query
                new_inputs: list = [user_input]

                for req in collected_requests:
                    print(f"\n[approval required]")
                    print(f"  Tool     : {req.function_call.name}")
                    print(f"  Arguments: {req.function_call.arguments}")
                    # Get user approval
                    answer = await asyncio.to_thread(input, "  Approve? (y/n): ")
                    approved = answer.strip().lower() == "y"

                    new_inputs.append(Message("assistant", [req]))
                    # Add the user's approval response
                    new_inputs.append(
                        Message("user", [req.to_function_approval_response(approved)])
                    )
                # Update input with all the context for next iteration
                current_input = new_inputs
        print()


if __name__ == "__main__":
    import sys
    if "--verbose" in sys.argv or "-v" in sys.argv:
        VERBOSE = True
        print("[verbose mode ON — tool calls will be shown]\n")
    if "--interactive" in sys.argv or "-i" in sys.argv:
        asyncio.run(interactive())
    else:
        asyncio.run(main())
