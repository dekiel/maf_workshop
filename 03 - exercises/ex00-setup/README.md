# Exercise 00 — Setup & Authentication

## Goal
Confirm your environment is ready and understand the two ways to authenticate
against a language model in this workshop.

---

## Client authentication methods

All exercises use the shared factory `create_chat_client()` which auto-selects the right backend based
on the environment variables in `.env`.

### Option 1 — Azure AI Foundry (recommended)
Uses **Azure AI Foundry Agent Service** with your Azure identity.
Requires an active `az login` session — no API key is needed.

```
# .env
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=gpt-4o
```

| Step | Command |
|------|---------|
| Log in | `az login` |
| Verify | `az account show` |

> **Required for Exercise 02** — `client.get_mcp_tool()` is only available on
> `FoundryChatClient` (the Responses API proxy). GitHub Models does not support it.

### Option 2 — GitHub Models
Uses the **GitHub Models** inference endpoint with a Personal Access Token.
No Azure subscription needed - ideal for local-only development.

```
# .env
GITHUB_PAT=github_pat_...
GITHUB_MODEL=gpt-4o
```
Create a token at <https://github.com/settings/tokens>.  
Required scopes: **read:user** (no write scopes needed for these exercises).

---

## Priority order in `create_chat_client()`

`create_chat_client()` checks env vars in this order and returns the first
matching backend:

1. **Foundry** — if `FOUNDRY_PROJECT_ENDPOINT` is set
2. **Azure OpenAI (API key)** — if `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` are set
3. **Azure OpenAI (AAD)** — if `AZURE_OPENAI_ENDPOINT` is set (uses `AzureCliCredential`)
4. **GitHub Models** — if `GITHUB_PAT` is set

You can switch backends at any time by commenting/uncommenting lines in `.env`.

---

## Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`
- At least one of the two options above configured in `.env`

## Run the setup check

```
python exercises/ex00-setup/verify_setup.py
```

The script validates packages, env vars, Azure credential (Foundry only), and
makes a live LLM call to confirm end-to-end connectivity.

Expected output (Foundry):
```
✅ Azure CLI credential
✅ Foundry endpoint reachable: <host>
✅ Live LLM call (FoundryChatClient): pong
All checks passed — you are ready to start!
```

Expected output (GitHub Models):
```
✅ Azure CLI credential: (skipped — using GitHub Models)
✅ Foundry endpoint reachable: (skipped — using GitHub Models)
✅ Live LLM call (OpenAIChatCompletionClient): pong
All checks passed — you are ready to start!
```
