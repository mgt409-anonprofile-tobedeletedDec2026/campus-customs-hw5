import { useEffect, useRef } from "react";
import { character } from "../characters";
import type { AgentEvent } from "../types";
import { Avatar } from "./Avatar";

export const TOOL_LABEL: Record<string, string> = {
  get_ticket: "reads the ticket",
  get_ticket_board: "checks the ticket board",
  check_stock_and_restock: "checks stock & vendors",
  check_bulk_order_pricing: "checks bulk pricing & margins",
  check_rent_due: "checks rent due",
  get_cash_position: "checks the cash position",
  list_payment_requests: "checks pending payment requests",
  list_drafts: "checks existing drafts",
  request_payment_approval: "asks David Wallace for a payment approval",
  save_draft_message: "saves a draft (not sent)",
  update_ticket_status: "updates the ticket status",
};

function FeedItem({ e }: { e: AgentEvent }) {
  const who = character(e.agent);
  if (e.event === "delegation") {
    const to = character(e.to);
    return (
      <li className="feed-handoff">
        <span className="handoff-names">
          <b style={{ color: who?.color }}>{who?.name.split(" ")[0]}</b>
          <span className="handoff-arrow" aria-label="asks">→</span>
          <b style={{ color: to?.color }}>{to?.name.split(" ")[0]}</b>
        </span>
        <span className="handoff-text">{e.said}</span>
      </li>
    );
  }
  if (e.event === "tool_call") {
    if (e.tool === "final_result" || e.tool === "ask_teammate") return null;
    return (
      <li className="feed-tool" style={{ borderColor: who?.color }}>
        <span aria-hidden="true">🔧</span> <b>{who?.name.split(" ")[0]}</b> {TOOL_LABEL[e.tool ?? ""] ?? "uses a tool"}{" "}
        <code>{e.tool}</code>
      </li>
    );
  }
  if ((e.event === "model_text" || e.event === "agent_end") && e.said && who) {
    return (
      <li className="feed-say">
        <Avatar who={who} size={44} />
        <div className="bubble" style={{ background: who.soft, borderColor: who.color, color: who.ink }}>
          <span className="bubble-name" style={{ color: who.color }}>
            {who.name} <small>· {who.role}</small>
            {e.event === "agent_end" && <span className="done-tag">done</span>}
          </span>
          <span>{e.said}</span>
          {e.event === "agent_end" && e.human_action && (
            <span className="bubble-human">💰 For David: {e.human_action}</span>
          )}
        </div>
      </li>
    );
  }
  if (e.event === "agent_start" && e.agent === "boss") {
    return <li className="feed-system">☕ Michael grabs ticket #{e.ticket_id} from the board.</li>;
  }
  if (e.event === "limit_hit") {
    return <li className="feed-warn">⚠️ Token guardrail: {who?.name ?? "An agent"} hit a limit and wrapped up.</li>;
  }
  if (e.event === "run_start") return <li className="feed-system">🔔 The team is on it.</li>;
  if (e.event === "ticket_resolved") return <li className="feed-system resolved">✅ Ticket resolved. The team's work is done.</li>;
  if (e.event === "run_end") {
    const err = (e.detail as { error?: string | null } | undefined)?.error;
    return err ? <li className="feed-warn">⚠️ Run stopped: {err}</li> : null;
  }
  return null;
}

// What every agent is saying and doing, newest at the bottom, refreshed by polling.
export function LiveFeed({ events, running, ticketId }: { events: AgentEvent[]; running: boolean; ticketId: number | null }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length]);

  return (
    <section className="panel feed" aria-labelledby="feed-title">
      <h2 id="feed-title">
        🗣️ Live from the office {ticketId !== null && <small>· ticket #{ticketId}</small>}
        {running && <span className="live-dot" aria-label="live">LIVE</span>}
      </h2>
      {ticketId === null ? (
        <p className="empty">Pick a ticket from the board to see what the team is up to.</p>
      ) : events.length === 0 ? (
        <p className="empty">Nobody has worked this ticket yet. Hit <b>Start the team</b>.</p>
      ) : (
        <ol className="feed-list" aria-live="polite">
          {events.map((e) => (
            <FeedItem key={e.index} e={e} />
          ))}
        </ol>
      )}
      <div ref={end} />
    </section>
  );
}
