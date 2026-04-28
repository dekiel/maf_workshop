# Exercise 02 — Agent with MCP: SAP Notes Researcher

## IMPORTANT
To be able to use "client.get_mcp_tool" a Foundry connection is required, iw tont work with Git PAT Token. 

## Goal
Extend the basic agent with a remote **Model Context Protocol (MCP)** server.

| File | MCP server | What it searches | Auth required |
|------|-----------|-----------------|---------------|
| `sap_notes_agent.py` | GitHub MCP (`api.githubcopilot.com`) | GitHub repos, issues, PRs | `GITHUB_PAT` token |

## What is MCP?
MCP (Model Context Protocol) is an open standard that lets agents connect to
external tool-servers without you writing individual wrappers. The agent
dynamically discovers what tools are available and calls them as needed.

## Concepts covered
- `client.get_mcp_tool(url=...)` — register a **remote** MCP server as a tool provider (Responses API)
- `async with Agent(...)` — context-manager form for proper connection cleanup
- Dynamic tool discovery from the MCP server
- Passing authentication headers to an MCP server (GitHub PAT)
- Mixing MCP tools and local `@tool` functions in the same agent
- `approval_mode="never_require"` is for workshop brevity. In production, use `"always_require"` for write operations.
- Non-streaming and streaming responses
- Interactive and non-interactive responses (run the script with `-i`)
- Verbose mode to print which local function is being called (run the script with `-v`)

## MCP transport comparison
| Transport | MAF class | When to use |
|-----------|-----------|-------------|
| Responses API proxy | `client.get_mcp_tool(url=...)` | MCP servers behind an OpenAI-compatible proxy (GitHub Copilot, etc.) |
| Remote Streamable HTTP | `MCPStreamableHTTPTool(url=...)` | Standard MCP servers (Microsoft Learn, etc.) |
| Local stdio | `MCPStdioTool(command=..., args=[...])` | Tools that run as a process (`npx`, `python`, etc.) |

## Prerequisites
- `.env` configured with `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL`
- `az login` completed
- `.env` configured with `GITHUB_PAT` (create at https://github.com/settings/tokens — needs `repo` and `read:org` scopes)

## Run

```bash
python exercises/ex02-agent-mcp/sap_notes_agent.py
python exercises/ex02-agent-mcp/sap_notes_agent.py --interactive
python exercises/ex02-agent-mcp/sap_notes_agent.py --interactive --verbose
```

## Exercises
1. Run `sap_notes_agent.py` as-is — observe how the agent searches GitHub repos.
2. Run an interactive session (`-i`) and chat freely.
3. Run with `-i -v` to see which local `@tool` functions are being called.
4. (Optional) Add an additional MCP server that searches official SAP documentation and SAP Community (SAP Docs MCP Server: https://mcp-sap-docs.marianzeis.de). Note that this MCP is not an official SAP MCP.

## Key takeaways
- MCP lets you connect to any compliant external service without writing adapters.
- `client.get_mcp_tool()` registers a remote MCP server via the Responses API proxy.
- Multiple tool sources (Python `@tool` + remote MCP) all work together in one agent.
- The `async with` form is important for `Agent` to ensure proper cleanup.
- `approval_mode` works on MCP tools just like on local `@tool` functions.

## Prompt examples

1. `What does BTP stand for in the SAP context?` — triggers local **lookup_sap_term**
2. `Find the top GitHub repositories related to SAP ABAP.` — triggers **GitHub MCP** search
3. `Search for open issues mentioning SAP BTP or SAP RISE.` — triggers **GitHub MCP** issues search
4. `List repositories from the SAP-samples organisation related to Fiori Elements.` — triggers **GitHub MCP**