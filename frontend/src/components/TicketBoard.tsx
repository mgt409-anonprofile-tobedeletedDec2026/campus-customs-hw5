import type { Ticket } from "../types";

const TYPE_LABEL: Record<string, { label: string; icon: string }> = {
  customer_order: { label: "Customer order", icon: "👕" },
  rent_notice: { label: "Rent notice", icon: "🏢" },
  price_override: { label: "Bulk discount", icon: "🧥" },
};

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

interface Props {
  tickets: Ticket[];
  selected: number | null;
  runningTicket: number | null;
  onSelect: (id: number) => void;
  onRun: (id: number) => void;
  busy: boolean;
}

// The ticket board: three sticky notes. Pick one, then start the team on it.
export function TicketBoard({ tickets, selected, runningTicket, onSelect, onRun, busy }: Props) {
  return (
    <section className="panel board" aria-labelledby="board-title">
      <h2 id="board-title">📌 Ticket board</h2>
      <ul className="tickets">
        {tickets.map((t, i) => {
          const kind = TYPE_LABEL[t.type] ?? { label: t.type, icon: "📄" };
          const running = runningTicket === t.id;
          const isSelected = selected === t.id;
          return (
            <li key={t.id} className={`ticket tilt-${i % 3} ${isSelected ? "selected" : ""}`}>
              <button
                type="button"
                className="ticket-pick"
                aria-pressed={isSelected}
                onClick={() => onSelect(t.id)}
              >
                <span className="ticket-id">#{t.id}</span>
                <span className="ticket-kind">{kind.icon} {kind.label}</span>
                <span className="ticket-subject">{t.subject}</span>
                {t.sku && (
                  <span className="ticket-meta">
                    {t.qty} × {t.sku} · size {t.size}
                  </span>
                )}
              </button>
              <div className="stickers">
                {running ? (
                  <span className="sticker working">⏳ Team working…</span>
                ) : t.state === "resolved" ? (
                  <span className="sticker resolved">✅ Resolved</span>
                ) : (
                  <span className="sticker open">📬 Open</span>
                )}
                {t.awaiting_david.length > 0 && (
                  <span className="sticker awaiting">
                    💰 Awaiting David · {money(t.awaiting_david.reduce((s, r) => s + r.amount, 0))}
                  </span>
                )}
              </div>
              <button
                type="button"
                className="btn btn-run"
                onClick={() => onRun(t.id)}
                disabled={busy}
                aria-label={`Start the agent team on ticket ${t.id}`}
              >
                {running ? "Working…" : t.state === "resolved" ? "Run again" : "Start the team"}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
