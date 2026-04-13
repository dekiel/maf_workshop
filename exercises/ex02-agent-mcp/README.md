# Exercise 02 — Agent with MCP: SAP Documentation Researcher

## Goal
Extend the basic agent with a remote **Model Context Protocol (MCP)** server.

| File | MCP server | What it searches | Auth required |
|------|-----------|-----------------|---------------|
| `sap_notes_agent.py` | Microsoft Learn MCP (`learn.microsoft.com/api/mcp`) | SAP-on-Azure docs, guides, tutorials | None (public) |

## What is MCP?
MCP (Model Context Protocol) is an open standard that lets agents connect to
external tool-servers without you writing individual wrappers. The agent
dynamically discovers what tools are available and calls them as needed.

## Concepts covered
- `MCPStreamableHTTPTool(url=...)` — connect to a **remote** Streamable-HTTP MCP server
- `async with Agent(...)` — context-manager form for proper connection cleanup
- Dynamic tool discovery from the MCP server
- Mixing MCP tools and local `@tool` functions in the same agent
- `approval_mode="never_require"` is for workshop brevity. In production, use `"always_require"` for write operations.
- Non-streaming and streaming responses
- Interactive and non-interactive responses (run the script with `-i`)
- Verbose mode to print which local function is being called (run the script with `-v`)

## MCP transport comparison
| Transport | MAF class | When to use |
|-----------|-----------|-------------|
| Remote Streamable HTTP | `MCPStreamableHTTPTool(url=...)` | Cloud-hosted servers (Microsoft Learn, etc.) |
| Local stdio | `MCPStdioTool(command=..., args=[...])` | Tools that run as a process (`npx`, `python`, etc.) |

## Prerequisites
- `.env` configured with `GITHUB_PAT` and `GITHUB_MODEL`

## Run

```bash
python exercises/ex02-agent-mcp/sap_notes_agent.py
python exercises/ex02-agent-mcp/sap_notes_agent.py --interactive
python exercises/ex02-agent-mcp/sap_notes_agent.py --interactive --verbose
```

## Exercises
1. Run `sap_notes_agent.py` as-is — observe how the agent searches Microsoft Learn docs.
2. Run an interactive session (`-i`) and chat freely about SAP on Azure.
3. Run with `-i -v` to see which local `@tool` functions are being called.
4. (Optional) Add an additional MCP server that searches official SAP documentation and SAP Community (SAP Docs MCP Server: https://mcp-sap-docs.marianzeis.de). Note that this MCP is not an official SAP MCP.

## Key takeaways
- MCP lets you connect to any compliant external service without writing adapters.
- `MCPStreamableHTTPTool` connects to standard Streamable-HTTP MCP servers.
- Multiple tool sources (Python `@tool` + remote MCP) all work together in one agent.
- The `async with` form is important for `Agent` to ensure proper cleanup.
- `approval_mode` works on MCP tools just like on local `@tool` functions.

## Prompt examples

1. `What does RISE stand for in the SAP context?` — triggers local **lookup_sap_term**
2. `Search for documentation about deploying SAP S/4HANA on Azure.` — triggers **Microsoft Learn MCP** search
3. `Find Microsoft Learn articles about RISE with SAP on Azure.` — triggers **Microsoft Learn MCP** search
4. `What are the best practices for running SAP workloads on Azure?` — triggers **Microsoft Learn MCP** search