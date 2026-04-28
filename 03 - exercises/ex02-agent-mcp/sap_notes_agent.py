"""
Exercise 02 — Agent with MCP: SAP Notes Researcher

This agent connects to the GitHub MCP server to search for developer-related
repositories, issues, and documentation directly from a conversational agent.
No manual function wrappers are needed — the agent discovers tools from the
MCP server dynamically.

Context
-----------
Developers regularly search GitHub for:
  - SAP open-source libraries (ABAP SDK, SAP Cloud SDK, CAP framework)
  - BTP-related issue trackers and pull requests
  - SAP sample code repositories for RISE migrations

This agent automates that search and can combine it with custom Python tools.

Prerequisites
-------------
Set in .env:
    FOUNDRY_PROJECT_ENDPOINT — your Azure AI Foundry project endpoint
    FOUNDRY_MODEL — model deployment name (e.g. gpt-4o)
    GITHUB_PAT — your GitHub Personal Access Token

References
----------
- MCP sample: https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/mcp/mcp_github_pat.py
- MCP overview: https://modelcontextprotocol.io/
"""

import asyncio
import functools
import json
import logging
import os
from typing import Annotated
from pathlib import Path
import sys

# Suppress noisy HTTP and framework logs — only show warnings and errors
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("agent_framework").setLevel(logging.WARNING)
logging.getLogger("exercises.shared.model_client").setLevel(logging.WARNING)

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework import Agent, Message, tool
from dotenv import load_dotenv
from pydantic import Field
from shared.model_client import create_chat_client

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

# A local @tool that complements the MCP tools
SAP_KEYWORD_GLOSSARY = {
    "ABAP": "Advanced Business Application Programming — SAP's proprietary language",
    "BTP": "SAP Business Technology Platform — PaaS offering for extensions and integrations",
    "RISE": "RISE with SAP — subscription bundle for moving core ERP to the cloud",
    "CAP": "Cloud Application Programming model — SAP's opinionated framework for Node.js/Java",
    "S4HANA": "SAP S/4HANA — next-generation ERP suite running on SAP HANA in-memory DB",
    "FIORI": "SAP Fiori — UX design system and app suite for SAP products",
}

@tool(approval_mode="never_require")
@_verbose_tool
def lookup_sap_term(
    term: Annotated[str, Field(description="SAP acronym or term to look up")],
) -> str:
    """Look up the definition of a common SAP acronym or technology term."""
    key = term.upper().replace(" ", "")
    definition = SAP_KEYWORD_GLOSSARY.get(key)
    if definition:
        return f"{term.upper()}: {definition}"
    return f"Term '{term}' not found in workshop glossary. Try the SAP Help Portal."

def _print_mcp_event(chunk) -> None:
    """Print a line when the agent invokes or receives a result from an MCP tool."""
    for content in getattr(chunk, "contents", None) or []:
        if getattr(content, "type", None) == "mcp_server_tool_call":
            print(f"\n[MCP] --> calling tool: {content.tool_name}", flush=True)
        elif getattr(content, "type", None) == "mcp_server_tool_result":
            print("[MCP] <-- tool result received", flush=True)

# Set to True via --verbose / -v at startup (see __main__)
VERBOSE: bool = False
# Main
async def main() -> None:
    # Load PAT for GitHub MCP authentication
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        raise ValueError(
            "GITHUB_PAT is not set. Create a token at https://github.com/settings/tokens "
            "and add it to your .env file."
        )

    auth_headers = {"Authorization": f"Bearer {github_pat}"}

    # Create the client (uses Azure AI Foundry + az login when FOUNDRY_PROJECT_ENDPOINT is set)
    client = create_chat_client()

    # get_mcp_tool() registers the GitHub remote MCP server.
    # The agent will discover its tools automatically at runtime.
    github_mcp_tool = client.get_mcp_tool(
        name="GitHub",
        url="https://api.githubcopilot.com/mcp/",
        headers=auth_headers,
        approval_mode="never_require",  # workshop convenience
    )

    async with Agent(
        client=client,
        name="SAPNotesResearcher",
        instructions=(
            "You are an SAP technology researcher. "
            "You help SAP developers find open-source repositories, code examples, "
            "and issues related to SAP technologies on GitHub. "
            "When asked about SAP acronyms, use the lookup_sap_term tool first. "
            "Be precise: always state the repository name and URL in your answers. "
            "IMPORTANT: Only answer using information returned by your tools. "
            "Do not use your general training knowledge, make up data, or perform any web search outside the provided tools. "
            "If none of your tools return relevant information, say you do not know."
        ),
        tools=[github_mcp_tool, lookup_sap_term],
    ) as agent:
        print("=== SAP Notes Researcher (MCP + GitHub) ===\n")

        # Query 1: Glossary lookup via local tool
        q1 = "What does BTP stand for in the SAP context?"
        print(f"User: {q1}")
        r1 = await agent.run(q1)
        print(f"Agent: {r1.text}\n")

        # Query 2: MCP — search GitHub for SAP repositories
        q2 = (
            "Find the top GitHub repositories related to SAP ABAP or SAP BTP."
        )
        print(f"User: {q2}")
        r2 = await agent.run(q2)
        print(f"Agent: {r2.text}\n")

        # Query 3: MCP — look for open issues
        q3 = (
            "Search open GitHub issues that mention 'SAP RISE' or 'RISE with SAP'"
        )
        print(f"User: {q3}")
        r3 = await agent.run(q3)
        print(f"Agent: {r3.text}\n")


async def interactive() -> None:
    """Interactive terminal loop — type your own questions."""
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        raise ValueError(
            "GITHUB_PAT is not set. Create a token at https://github.com/settings/tokens "
            "and add it to your .env file."
        )

    auth_headers = {"Authorization": f"Bearer {github_pat}"}

    client = create_chat_client()

    github_mcp_tool = client.get_mcp_tool(
        name="GitHub",
        url="https://api.githubcopilot.com/mcp/",
        headers=auth_headers,
        approval_mode="never_require",
    )

    async with Agent(
        client=client,
        name="SAPNotesResearcher",
        instructions=(
            "You are an SAP technology researcher. "
            "You help SAP developers find open-source repositories, code examples, "
            "and issues related to SAP technologies on GitHub. "
            "When asked about SAP acronyms, use the lookup_sap_term tool first. "
            "Be precise: always state the repository name and URL in your answers. "
            "IMPORTANT: Only answer using information returned by your tools. "
            "Do not use your general training knowledge, make up data, or perform any web search outside the provided tools. "
            "If none of your tools return relevant information, say you do not know."
        ),
        tools=[github_mcp_tool, lookup_sap_term],
    ) as agent:
        print("=== SAP Notes Researcher — interactive mode ===")
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
                async for chunk in agent.run(current_input, stream=True): ## Async iteration — process updates as they arrive for real-time display (see https://learn.microsoft.com/en-us/agent-framework/agents/running-agents?pivots=programming-language-python)
                    _print_mcp_event(chunk)
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                    if chunk.user_input_requests:
                        collected_requests.extend(chunk.user_input_requests)
                print()

                if collected_requests:
                    pending_approvals = True
                    new_inputs: list = [user_input]

                    for req in collected_requests:
                        print(f"\n[approval required]")
                        print(f"  Tool     : {req.function_call.name}")
                        print(f"  Arguments: {req.function_call.arguments}")
                        answer = await asyncio.to_thread(input, "  Approve? (y/n): ")
                        approved = answer.strip().lower() == "y"

                        new_inputs.append(Message("assistant", [req]))
                        new_inputs.append(
                            Message("user", [req.to_function_approval_response(approved)])
                        )

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
