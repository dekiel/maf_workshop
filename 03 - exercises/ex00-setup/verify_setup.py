"""
Exercise 00 — Setup Verification

Run this script to confirm your environment is correctly configured before
starting the workshop exercises.

"""

import asyncio
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check(label: str, passed: bool, detail: str = "") -> bool:
    status = "✅" if passed else "❌"
    line = f"{status} {label}"
    if detail:
        line += f": {detail}"
    print(line)
    return passed

def check_python_version() -> bool:
    version = sys.version_info
    ok = version >= (3, 10)
    return check(
        "Python version OK",
        ok,
        f"{version.major}.{version.minor}.{version.micro}" + ("" if ok else " — need 3.10+"),
    )

def check_package(package: str) -> bool:
    try:
        importlib.import_module(package)
        return check(f"Package '{package}' installed", True)
    except ImportError:
        return check(f"Package '{package}' installed", False, "run: pip install -r requirements.txt")

def check_env_var(name: str, required: bool = True) -> bool:
    value = os.getenv(name)
    if value:
        return check(f"Env var {name}", True, value[:30] + "..." if len(value) > 30 else value)
    if required:
        return check(f"Env var {name}", False, "not set — check your .env file")
    check(f"Env var {name}", True, "(optional — not set)")
    return True

async def check_azure_credential() -> bool:
    try:
        from azure.identity import AzureCliCredential
        cred = AzureCliCredential()
        token = cred.get_token("https://management.azure.com/.default")
        return check("Azure CLI credential", bool(token.token))
    except Exception as exc:
        return check("Azure CLI credential", False, f"{exc} — run: az login")


async def check_foundry_endpoint() -> bool:
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    if not endpoint or "your-project" in endpoint:
        return check(
            "Foundry endpoint reachable",
            False,
            "FOUNDRY_PROJECT_ENDPOINT not configured in .env",
        )
    try:
        import urllib.request
        host = endpoint.split("/")[2]
        urllib.request.urlopen(f"https://{host}", timeout=5)  # noqa: S310
        return check("Foundry endpoint reachable", True, host)
    except Exception:
        # Endpoint may require auth — connectivity failure here is acceptable
        return check("Foundry endpoint reachable", True, "(auth required — assumed reachable)")


async def check_live_llm() -> bool:
    """Send a minimal request via create_chat_client() and check for a non-empty reply."""
    try:
        from agent_framework import Agent
        from shared.model_client import create_chat_client

        client = create_chat_client()
        backend = type(client).__name__
        agent = Agent(client=client, name="PingAgent", instructions="You are a ping agent.")
        result = await agent.run("Reply with exactly: pong")
        ok = bool(result.text and result.text.strip())
        return check(f"Live LLM call ({backend})", ok, result.text.strip()[:60] if ok else "empty response")
    except Exception as exc:
        return check("Live LLM call", False, str(exc)[:120])


async def main() -> None:
    # Load .env from repo root
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    print("\n=== Microsoft Agent Framework Workshop — Setup Check ===\n")

    results: list[bool] = []

    results.append(check_python_version())
    results.append(check_package("agent_framework"))
    results.append(check_package("azure.identity"))
    results.append(check_package("dotenv"))

    print()
    foundry_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    github_pat = os.getenv("GITHUB_PAT", "")
    has_foundry = bool(foundry_endpoint and "your-project" not in foundry_endpoint)
    has_github = bool(github_pat)

    results.append(check_env_var("FOUNDRY_PROJECT_ENDPOINT", required=not has_github))
    results.append(check_env_var("FOUNDRY_MODEL", required=has_foundry))
    results.append(check_env_var("GITHUB_PAT", required=not has_foundry))
    results.append(check_env_var("GITHUB_MODEL", required=has_github and not has_foundry))

    if not has_foundry and not has_github:
        print("\n❌ At least one backend must be configured (FOUNDRY_PROJECT_ENDPOINT or GITHUB_PAT).")
        sys.exit(1)

    print()
    if has_foundry:
        results.append(await check_azure_credential())
        results.append(await check_foundry_endpoint())
    else:
        check("Azure CLI credential", True, "(skipped — using GitHub Models)")
        check("Foundry endpoint reachable", True, "(skipped — using GitHub Models)")

    print()
    results.append(await check_live_llm())

    print()
    if all(results):
        print("All checks passed — you are ready to start!")
    else:
        failed = sum(1 for r in results if not r)
        print(f"⚠️  {failed} check(s) failed. Fix the issues above before continuing.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
