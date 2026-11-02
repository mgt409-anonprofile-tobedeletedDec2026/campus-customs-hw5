"""The Campus Customs agent team: five PydanticAI agents that share one MCP server.

* Every shop fact and every board change goes through the campus-customs MCP
  server (mcp_server/server.py). There is no second tools layer.
* Each agent only sees the MCP tools on its allowlist (TOOL_ACCESS). The
  human_* pay/decline tools are never on any list.
* Any agent can ask any other agent for help (ask_teammate), within the limits
  in config.py: delegation depth, two asks per pair per ticket, and a shared
  model-request and token budget per ticket.
* Every step is appended to output/audit_trail.json.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Any
from uuid import uuid4

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from openai import AsyncOpenAI  # noqa: E402
from pydantic_ai import Agent, RunContext  # noqa: E402
from pydantic_ai.exceptions import UsageLimitExceeded  # noqa: E402
from pydantic_ai.mcp import MCPToolset  # noqa: E402
from pydantic_ai.messages import RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart  # noqa: E402
from pydantic_ai.models.openai import OpenAIResponsesModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from pydantic_ai.usage import RunUsage, UsageLimits  # noqa: E402

import audit  # noqa: E402
from config import (  # noqa: E402
    HUMAN_APPROVER,
    MAX_CALLS_PER_PAIR,
    MAX_DELEGATION_DEPTH,
    MAX_MODEL_REQUESTS_PER_AGENT_RUN,
    MAX_MODEL_REQUESTS_PER_TICKET,
    MAX_TOKENS_PER_TICKET,
    MCP_SERVER_FILE,
    OPENAI_MODEL,
    PORTKEY_BASE_URL,
    PROMPTS_DIR,
    portkey_api_key,
)
from models import AGENT_TITLES, AgentDeps, AgentName, AgentReport, TeamState, TicketRunResult  # noqa: E402

# Which MCP tools each agent may use (least privilege). Nobody gets human_* tools.
TOOL_ACCESS: dict[str, set[str]] = {
    "boss": {"get_ticket_board", "get_ticket", "get_cash_position", "list_payment_requests",
             "list_drafts", "update_ticket_status"},
    "inventory": {"get_ticket", "check_stock_and_restock", "check_bulk_order_pricing"},
    "accounting": {"get_ticket", "get_cash_position", "check_rent_due", "check_bulk_order_pricing",
                   "check_stock_and_restock", "list_payment_requests", "request_payment_approval",
                   "assess_payment_request"},
    "facilities": {"get_ticket", "check_rent_due", "get_cash_position"},
    "customer_service": {"get_ticket", "list_drafts", "save_draft_message"},
}
assert not any(t.startswith("human_") for tools in TOOL_ACCESS.values() for t in tools)

# Tool arguments that name the acting agent. The backend fills these in, so an
# agent cannot sign a status change, draft, or payment request as someone else.
IDENTITY_ARGS = ("agent", "author_agent", "requested_by")


def _load_mcp_server():
    spec = importlib.util.spec_from_file_location("campus_customs_mcp", MCP_SERVER_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.mcp


async def _stamp_identity(ctx: RunContext[AgentDeps], call_tool, name: str, args: dict[str, Any]):
    if name.startswith("human_") or name not in TOOL_ACCESS[ctx.deps.agent]:
        raise PermissionError(f"{ctx.deps.agent} is not allowed to call {name}.")
    for key in IDENTITY_ARGS:
        if key in args:
            args[key] = ctx.deps.agent
    return await call_tool(name, args)


MCP_SERVER = _load_mcp_server()  # also used by main.py for the human-only routes
SHOP_MCP = MCPToolset(MCP_SERVER, process_tool_call=_stamp_identity)

_model: OpenAIResponsesModel | None = None


def _get_model() -> OpenAIResponsesModel:
    """gpt-6-luna through Portkey (the only model this project may use)."""
    global _model
    if _model is None:
        key = portkey_api_key()
        client = AsyncOpenAI(api_key=key, base_url=PORTKEY_BASE_URL,
                             default_headers={"x-portkey-api-key": key})
        _model = OpenAIResponsesModel(OPENAI_MODEL, provider=OpenAIProvider(openai_client=client))
    return _model


async def ask_teammate(ctx: RunContext[AgentDeps], teammate: AgentName, request: str) -> str:
    """Ask another Campus Customs agent to do part of the work or answer a question.

    teammate: boss, inventory, accounting, facilities, or customer_service.
    request: a clear, specific ask with the ticket number and any numbers they need.

    Limits: you may ask the same teammate at most twice per ticket, and
    hand-offs can only go a few levels deep. If a limit is hit, finish with what
    you have and flag it for the human.
    """
    me, team = ctx.deps.agent, ctx.deps.team
    if teammate == me:
        return "You can't delegate to yourself. Do the work or ask a different teammate."
    if ctx.deps.depth + 1 > MAX_DELEGATION_DEPTH:
        audit.record(team.run_id, team.ticket_id, me, "limit_hit", limit="delegation_depth", to=teammate)
        return (f"Delegation limit reached (max depth {MAX_DELEGATION_DEPTH}). "
                "Finish with what you know and flag anything missing for the human.")
    pair = (me, teammate)
    if team.pair_calls[pair] >= MAX_CALLS_PER_PAIR:
        audit.record(team.run_id, team.ticket_id, me, "limit_hit", limit="calls_per_pair", to=teammate)
        return (f"You have already asked {teammate} {MAX_CALLS_PER_PAIR} times on this ticket. "
                "Use their earlier answers.")
    if team.requests_used() >= MAX_MODEL_REQUESTS_PER_TICKET:
        audit.record(team.run_id, team.ticket_id, me, "limit_hit", limit="requests_per_ticket", to=teammate)
        return "This ticket's model-request budget is used up. Finish with what you know and flag it for the human."
    team.pair_calls[pair] += 1
    audit.record(team.run_id, team.ticket_id, me, "delegation", to=teammate, request=request,
                 depth=ctx.deps.depth + 1, ask_number=team.pair_calls[pair])
    sub_deps = AgentDeps(agent=teammate, depth=ctx.deps.depth + 1, team=team)
    prompt = f"{AGENT_TITLES[me]} asks you, on ticket #{team.ticket_id}: {request}"
    try:
        report = await run_agent(teammate, prompt, sub_deps)
    except UsageLimitExceeded as exc:
        audit.record(team.run_id, team.ticket_id, teammate, "limit_hit", limit="usage", detail=str(exc))
        return f"{teammate} ran out of its request/token budget ({exc}). Flag this for the human."
    audit.record(team.run_id, team.ticket_id, me, "delegation_result", from_agent=teammate,
                 report=report.model_dump())
    return report.model_dump_json()


def _build_agent(name: str) -> Agent[AgentDeps, AgentReport]:
    allowed = TOOL_ACCESS[name]
    agent: Agent[AgentDeps, AgentReport] = Agent(
        _get_model(),
        name=name,
        instructions=(PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8"),
        deps_type=AgentDeps,
        output_type=AgentReport,
        toolsets=[SHOP_MCP.filtered(lambda ctx, tool_def, allowed=allowed: tool_def.name in allowed)],
    )

    @agent.instructions
    def run_context(ctx: RunContext[AgentDeps]) -> str:
        return (f"You are working ticket #{ctx.deps.team.ticket_id}. Your agent id is {name}. "
                f"Delegation depth: {ctx.deps.depth} of {MAX_DELEGATION_DEPTH}. "
                f"The only human approver is {HUMAN_APPROVER}.")

    agent.tool(ask_teammate)
    return agent


_team: dict[str, Agent[AgentDeps, AgentReport]] = {}


def team() -> dict[str, Agent[AgentDeps, AgentReport]]:
    if not _team:
        _team.update({name: _build_agent(name) for name in TOOL_ACCESS})
    return _team


async def run_agent(name: str, prompt: str, deps: AgentDeps) -> AgentReport:
    """Run one agent's loop, appending each step to the audit trail.

    Each agent turn has its own budget (MAX_MODEL_REQUESTS_PER_AGENT_RUN), capped
    by what is left of the whole ticket's budget, which all agents share.
    """
    t = deps.team
    requests_left = MAX_MODEL_REQUESTS_PER_TICKET - t.requests_used()
    tokens_left = MAX_TOKENS_PER_TICKET - t.tokens_used()
    if requests_left <= 0 or tokens_left <= 0:
        raise UsageLimitExceeded("This ticket's request/token budget is used up.")
    limits = UsageLimits(request_limit=min(MAX_MODEL_REQUESTS_PER_AGENT_RUN, requests_left),
                         total_tokens_limit=tokens_left)
    usage = RunUsage()
    t.active_usage.append(usage)
    audit.record(t.run_id, t.ticket_id, name, "agent_start", depth=deps.depth, prompt=prompt)
    try:
        report = await _iterate(name, prompt, deps, usage, limits, t)
    finally:
        t.active_usage.remove(usage)
        t.finished_requests += usage.requests
        t.finished_tokens += usage.total_tokens
    audit.record(t.run_id, t.ticket_id, name, "agent_end", report=report.model_dump(),
                 agent_requests=usage.requests, agent_tokens=usage.total_tokens,
                 ticket_requests_so_far=t.requests_used(), ticket_tokens_so_far=t.tokens_used())
    return report


async def _iterate(name: str, prompt: str, deps: AgentDeps, usage: RunUsage,
                   limits: UsageLimits, t: TeamState) -> AgentReport:
    step = 0
    async with team()[name].iter(prompt, deps=deps, usage=usage, usage_limits=limits) as run:
        async for node in run:
            if Agent.is_call_tools_node(node):
                step += 1
                for part in node.model_response.parts:
                    if isinstance(part, TextPart) and part.content.strip():
                        audit.record(t.run_id, t.ticket_id, name, "model_text", step=step, text=part.content)
                    elif isinstance(part, ToolCallPart):
                        audit.record(t.run_id, t.ticket_id, name, "tool_call", step=step,
                                     tool=part.tool_name, args=part.args_as_dict())
            elif Agent.is_model_request_node(node):
                for part in node.request.parts:
                    if isinstance(part, ToolReturnPart):
                        audit.record(t.run_id, t.ticket_id, name, "tool_result", step=step,
                                     tool=part.tool_name, output=part.content)
                    elif isinstance(part, RetryPromptPart):
                        audit.record(t.run_id, t.ticket_id, name, "tool_retry", step=step,
                                     tool=part.tool_name, detail=part.model_response())
    return run.result.output


def new_run_id() -> str:
    return uuid4().hex[:12]


async def run_ticket(ticket_id: int, run_id: str | None = None) -> TicketRunResult:
    """Michael (Boss) takes one ticket from the board and leads the team on it."""
    run_id = run_id or new_run_id()
    team_state = TeamState(run_id=run_id, ticket_id=ticket_id)
    deps = AgentDeps(agent="boss", depth=0, team=team_state)
    audit.record(run_id, ticket_id, None, "run_start", model=OPENAI_MODEL, limits={
        "requests_per_ticket": MAX_MODEL_REQUESTS_PER_TICKET,
        "requests_per_agent_run": MAX_MODEL_REQUESTS_PER_AGENT_RUN,
        "tokens_per_ticket": MAX_TOKENS_PER_TICKET,
        "delegation_depth": MAX_DELEGATION_DEPTH,
        "calls_per_pair": MAX_CALLS_PER_PAIR,
    })
    report, error = None, None
    prompt = (f"Ticket #{ticket_id} is on the board. Read it, decide who works on it, delegate, "
              "make the final call, set the ticket status, and report. Anything involving money "
              f"must end as a payment request for {HUMAN_APPROVER}, never a payment.")
    try:
        async with SHOP_MCP:
            report = await run_agent("boss", prompt, deps)
    except UsageLimitExceeded as exc:
        error = f"Stopped by token guardrail: {exc}"
    except Exception as exc:  # recorded so the audit shows every failed run too
        error = f"{type(exc).__name__}: {exc}"
    requests, tokens = team_state.requests_used(), team_state.tokens_used()
    audit.record(run_id, ticket_id, None, "run_end", error=error, model_requests=requests, total_tokens=tokens)
    return TicketRunResult(run_id=run_id, ticket_id=ticket_id, report=report, error=error,
                           model_requests=requests, total_tokens=tokens)
