"""Data types shared by the Campus Customs agent team."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
TicketStatus = Literal["open", "in_progress", "waiting_on_human", "blocked", "resolved"]

AGENT_TITLES: dict[str, str] = {
    "boss": "Michael Scott (Boss)",
    "inventory": "Dwight Schrute (Inventory)",
    "accounting": "Oscar Martinez (Accounting)",
    "facilities": "Darryl Philbin (Facilities)",
    "customer_service": "Pam Beesly (Customer Service)",
}


class AgentReport(BaseModel):
    """What every agent hands back when it finishes its turn."""

    agent: AgentName
    summary: str = Field(description=(
        "Two or three sentences in your character's own voice: open with one short, fun in-character "
        "line, then the key facts and numbers. This is what the dashboard shows David Wallace."
    ))
    findings: list[str] = Field(default_factory=list, description="Facts from the tools, with numbers.")
    actions_taken: list[str] = Field(default_factory=list, description="Tool actions that changed the board.")
    needs_human: bool = Field(description="True if David Wallace must approve or decide something.")
    human_action: str | None = Field(default=None, description="Exactly what the human must decide, if anything.")
    payment_request_ids: list[int] = Field(default_factory=list)
    draft_ids: list[int] = Field(default_factory=list)
    rules_checked: list[str] = Field(default_factory=list, description="Shop rules that applied and how you followed them.")


class TicketRunResult(BaseModel):
    """One full Boss-led run on a ticket."""

    run_id: str
    ticket_id: int
    report: AgentReport | None
    error: str | None = None
    model_requests: int
    total_tokens: int


class LoginBody(BaseModel):
    password: str


class DecisionBody(BaseModel):
    """David Wallace's reason for approving or declining a payment request."""

    reason: str = Field(default="", max_length=500)
    acknowledge_risk: bool = Field(
        default=False, description="David ticked 'I understand, pay anyway' on Oscar's priority warning.")


@dataclass
class TeamState:
    """Shared by every agent working on one ticket in one run."""

    run_id: str
    ticket_id: int
    pair_calls: Counter = field(default_factory=Counter)  # (caller, callee) -> times asked
    finished_requests: int = 0   # model requests by agent turns that have ended
    finished_tokens: int = 0
    active_usage: list = field(default_factory=list)      # RunUsage of agent turns still running

    def requests_used(self) -> int:
        return self.finished_requests + sum(u.requests for u in self.active_usage)

    def tokens_used(self) -> int:
        return self.finished_tokens + sum(u.total_tokens for u in self.active_usage)


@dataclass
class AgentDeps:
    """Per-agent context passed to tools."""

    agent: AgentName
    depth: int
    team: TeamState
