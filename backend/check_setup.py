"""Check that the agent team starts and connects, without running any tickets.

    .venv\\Scripts\\python.exe backend\\check_setup.py

1. Config: the model is gpt-6-luna and the Portkey key is present (never printed).
2. MCP: the campus-customs server starts and lists its tools.
3. Access: every agent's allowed tools exist, and no agent can see a human_ tool.
4. Team: all five agents build.
5. Portkey: one tiny model call confirms the key and model work.
6. Database: the working copy is byte-for-byte unchanged by these checks.
"""

import asyncio
import hashlib

from fastmcp import Client
from pydantic_ai import Agent

import agents
from config import OPENAI_MODEL, ORIGINAL_DB, WORKING_DB, portkey_api_key


def _md5(path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


async def main() -> None:
    before = _md5(WORKING_DB)
    portkey_api_key()
    print(f"[ok] model = {OPENAI_MODEL}; PORTKEY_API_KEY is set (value not shown)")

    async with Client(agents._load_mcp_server()) as client:
        tools = sorted(t.name for t in await client.list_tools())
    print(f"[ok] MCP server started: {len(tools)} tools: {', '.join(tools)}")

    for name, allowed in agents.TOOL_ACCESS.items():
        missing = allowed - set(tools)
        assert not missing, f"{name} is allowed tools the server lacks: {missing}"
        assert not any(t.startswith("human_") for t in allowed)
        print(f"[ok] {name:<16} -> {', '.join(sorted(allowed))} + ask_teammate")
    human_only = [t for t in tools if t.startswith("human_")]
    print(f"[ok] human-only tools, given to no agent: {', '.join(human_only)}")

    team = agents.team()
    print(f"[ok] built {len(team)} agents: {', '.join(team)}")

    ping = Agent(agents._get_model(), instructions="Reply with exactly: OK")
    reply = await ping.run("ping")
    print(f"[ok] Portkey -> {OPENAI_MODEL} replied: {reply.output.strip()!r}")

    after = _md5(WORKING_DB)
    assert before == after, "The working database changed during the check!"
    same = after == _md5(ORIGINAL_DB)
    print(f"[ok] working database unchanged (md5 {after}); matches original: {same}")


if __name__ == "__main__":
    asyncio.run(main())
