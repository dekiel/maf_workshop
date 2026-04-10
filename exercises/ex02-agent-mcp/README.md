# Exercise 02 — Agent with MCP: SAP Notes Researcher + SAP Docs Researcher

## Goal
Extend the basic agent with remote **Model Context Protocol (MCP)** servers.
Two sample files show how to connect to different MCP servers using the same pattern:

| File | MCP server | What it searches | Auth required |
|------|-----------|-----------------|---------------|
| `sap_notes_agent.py` | GitHub MCP (`api.githubcopilot.com`) | GitHub repos, issues, PRs | `GITHUB_PAT` token |
| `sap_docs_agent.py` | SAP Docs MCP (`mcp-sap-docs.marianzeis.de`) | SAP official docs + SAP Community | None |
| `sap_cap_agent.py` | `@cap-js/mcp-server` (local stdio, `npx`) | **Your** CDS model + CAP docs | Node.js + `npx` |

## What is MCP?
MCP (Model Context Protocol) is an open standard that lets agents connect to
external tool-servers without you writing individual wrappers. The agent
dynamically discovers what tools are available and calls them as needed.
Think of it like giving your agent an SAP-style RFC destination, but for any
web service.

## Concepts covered
- `client.get_mcp_tool(url=...)` — register a **remote** MCP server as a tool provider
- `MCPStdioTool(command=..., args=[...])` — launch a **local** MCP server as a child process
- `async with mcp_tool:` — context-manager that starts/stops the stdio process cleanly
- `async with Agent(...)` — context-manager form for proper connection cleanup
- Dynamic tool discovery from both remote and local MCP servers
- Passing authentication headers to an MCP server (GitHub PAT example)
- Connecting to a public MCP server with no authentication (SAP Docs example)
- Mixing remote/local MCP tools and local `@tool` functions in the same agent
- `approval_mode="never_require"` is for workshop brevity. In production, use `"always_require"` for write operations.
- Non-streaming and streaming responses
- Interactive and non-interactive responses (run the script with `-i`)
- Verbose mode to print which local function is being called (run the script with `-v`)

## MCP transport comparison
| Transport | MAF class | When to use |
|-----------|-----------|-------------|
| Remote HTTPS/SSE | `client.get_mcp_tool(url=...)` | Cloud-hosted servers (GitHub, SAP Docs, etc.) |
| Local stdio | `MCPStdioTool(command=..., args=[...])` | Tools that run as a process (`npx`, `python`, etc.) |

## Prerequisites
- `.env` configured with `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL`
- `az login` completed
- **For `sap_notes_agent.py` only:** `.env` configured with `GITHUB_PAT` (create at https://github.com/settings/tokens — needs `repo` and `read:org` scopes)
- **For `sap_cap_agent.py` only:** Node.js ≥ 18 + `npx` on PATH (`node --version && npx --version`). Set `CAP_PROJECT_DIR` in `.env` to your CAP project path, or run from inside the project folder.

## Run

### SAP Docs Researcher (SAP Docs MCP — no auth needed, start here)
```bash
python exercises/ex02-agent-mcp/sap_docs_agent.py
python exercises/ex02-agent-mcp/sap_docs_agent.py --interactive
python exercises/ex02-agent-mcp/sap_docs_agent.py --interactive --verbose
```

### SAP CAP Developer Assistant (local stdio MCP — needs Node.js + a CAP project)
```bash
# From inside a CAP project directory:
python exercises/ex02-agent-mcp/sap_cap_agent.py
python exercises/ex02-agent-mcp/sap_cap_agent.py --interactive
python exercises/ex02-agent-mcp/sap_cap_agent.py --interactive --verbose

# Or point to any CAP project:
# Add CAP_PROJECT_DIR=/path/to/your/cap/project to .env
```

### SAP Notes Researcher (GitHub MCP — requires GITHUB_PAT)
```bash
python exercises/ex02-agent-mcp/sap_notes_agent.py
python exercises/ex02-agent-mcp/sap_notes_agent.py --interactive
python exercises/ex02-agent-mcp/sap_notes_agent.py --interactive --verbose
```

## Exercises
1. Run `sap_docs_agent.py` as-is — no token needed. Observe how the agent searches SAP official docs.
2. Run `sap_notes_agent.py` as-is — observe how the agent searches GitHub repos instead.
3. Run `sap_cap_agent.py` from inside a CAP project — ask it about entities and services in your own model.
4. Run an interactive session on any agent (`-i`) and chat freely.
5. Run with `-i -v` to see which local `@tool` functions are being called.
6. (Optional) Change `approval_mode` to `"always_require"` on any MCP tool — the agent will pause before each call and ask for your approval.
7. (Optional) Combine two MCP servers in one agent by adding both to the `tools` list — observe how the LLM picks the right source per question.

## Key takeaways
- MCP lets you connect to any compliant external service without writing adapters.
- Remote MCP servers (`get_mcp_tool`) and local stdio servers (`MCPStdioTool`) use the same `tools=` list — the agent doesn't need to know which is which.
- Multiple tool sources (Python `@tool` + remote MCP + local stdio MCP) all work together in one agent.
- The `async with` form is important for both `Agent` and `MCPStdioTool` to ensure process cleanup.
- `approval_mode` works on MCP tools just like on local `@tool` functions.

## Example questions

1. `What does BTP stand for in the SAP context?` — triggers local **lookup_sap_term**
2. `Find the top GitHub repositories related to SAP ABAP.` — triggers **GitHub MCP** search
3. `Search for open issues mentioning SAP BTP or SAP RISE.` — triggers **GitHub MCP** issues search
4. `What is CAP and find me the latest open pull requests in the SAP Cloud Application Programming Model repo.` — triggers **lookup_sap_term** then **GitHub MCP**
5. `List repositories from the SAP-samples organisation related to Fiori Elements.` — triggers **GitHub MCP**

