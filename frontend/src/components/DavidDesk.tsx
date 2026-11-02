import { useState } from "react";
import { api, ApiError } from "../api";
import { CHARACTERS } from "../characters";
import type { PaymentRequest } from "../types";
import { Avatar } from "./Avatar";

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });
const KIND: Record<string, string> = { invoice: "Vendor invoice", rent: "Rent", purchase_order: "Purchase order" };

interface Props {
  loggedIn: boolean;
  requests: PaymentRequest[];
  onLogin: (password: string) => Promise<void>;
  onLogout: () => void;
  onDecided: () => void;
  onReset: () => Promise<void>;
  runBusy: boolean;
}

function RequestCard({ r, onDecided }: { r: PaymentRequest; onDecided: () => void }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<"approve" | "decline" | null>(null);
  const [refusal, setRefusal] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const requester = r.requested_by === "accounting" ? "Oscar" : r.requested_by;
  const atRisk = r.risk?.at_risk ?? false;

  async function decide(kind: "approve" | "decline") {
    setBusy(kind);
    setError(null);
    setRefusal(null);
    try {
      if (kind === "approve") await api.approve(r.id, reason, acknowledged);
      else await api.decline(r.id, reason);
      onDecided();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (e instanceof ApiError && e.status === 409 && msg.startsWith("Oscar")) setRefusal(msg);
      else setError(msg);
    } finally {
      setBusy(null);
    }
  }

  return (
    <li className="request">
      <div className="request-top">
        <span className="request-kind">{KIND[r.kind] ?? r.kind} · ticket #{r.ticket_id}</span>
        <span className="request-amount">{money(r.amount)}</span>
      </div>
      <p className="request-why">
        <b>{requester} asks:</b> {r.reason}
        {r.kind === "purchase_order" && r.qty && <> ({r.qty} × {r.sku} size {r.size})</>}
      </p>
      {atRisk && r.risk && (
        <div className="oscar-warning" role="alert">
          <Avatar who={CHARACTERS.accounting} size={40} />
          <div>
            <p className="warning-title">⚠️ Rent protection: a more important bill is at risk</p>
            <p>{r.risk.warning}</p>
            <ol className="priority-order">
              {r.risk.recommended_order.map((o) => (
                <li key={o.label} className={o.affordable ? "" : "short"}>
                  {o.label}: <em>{o.why}</em>{" "}
                  {o.affordable ? `→ cash ${money(o.cash_after)}` : "→ can't be covered"}
                </li>
              ))}
            </ol>
            <label className="ack">
              <input type="checkbox" checked={acknowledged} onChange={(e) => setAcknowledged(e.target.checked)} />
              I understand, pay anyway
            </label>
          </div>
        </div>
      )}
      <label className="field">
        <span>David's reason</span>
        <textarea
          rows={2}
          value={reason}
          maxLength={500}
          placeholder="e.g. Rent keeps us in the building, so pay it first."
          onChange={(e) => setReason(e.target.value)}
        />
      </label>
      <div className="request-actions">
        <button
          type="button"
          className="btn btn-approve"
          disabled={busy !== null || (atRisk && !acknowledged)}
          title={atRisk && !acknowledged ? "Tick 'I understand, pay anyway' first" : undefined}
          onClick={() => decide("approve")}
        >
          {busy === "approve" ? "Paying…" : "✅ Approve & pay"}
        </button>
        <button type="button" className="btn btn-decline" disabled={busy !== null} onClick={() => decide("decline")}>
          {busy === "decline" ? "Declining…" : "✋ Decline"}
        </button>
      </div>
      {refusal && (
        <div className="oscar-refusal" role="alert">
          <Avatar who={CHARACTERS.accounting} size={40} />
          <p>{refusal}</p>
        </div>
      )}
      {error && <p className="error" role="alert">{error}</p>}
    </li>
  );
}

// David Wallace's desk: login, the approval inbox, and the reset button.
export function DavidDesk({ loggedIn, requests, onLogin, onLogout, onDecided, onReset, runBusy }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onLogin(password);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    setBusy(true);
    setError(null);
    try {
      await onReset();
      setConfirmReset(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel david" aria-labelledby="david-title">
      <header className="david-head">
        <Avatar who={CHARACTERS.david} size={52} />
        <div>
          <h2 id="david-title">David Wallace's desk</h2>
          <p className="role">🖊️ The only one who can approve money</p>
        </div>
      </header>

      {!loggedIn ? (
        <form className="login" onSubmit={submit}>
          <label className="field">
            <span>Approver password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy || !password}>
            {busy ? "Checking…" : "🔐 Log in as David"}
          </button>
          {error && <p className="error" role="alert">{error}</p>}
          <p className="hint">Agents can prepare payments, but only David can approve them.</p>
        </form>
      ) : (
        <>
          <div className="inbox-head">
            <h3>📥 Approval inbox</h3>
            <button type="button" className="link" onClick={onLogout}>Log out</button>
          </div>
          {requests.length === 0 ? (
            <p className="empty">Nothing waiting. Enjoy your coffee. ☕</p>
          ) : (
            <ul className="requests">
              {requests.map((r) => <RequestCard key={r.id} r={r} onDecided={onDecided} />)}
            </ul>
          )}
          <div className="fire-drill">
            {!confirmReset ? (
              <button type="button" className="btn btn-reset" disabled={busy || runBusy} onClick={() => setConfirmReset(true)}>
                🔥 Reset database (fire drill)
              </button>
            ) : (
              <div className="confirm" role="alertdialog" aria-label="Confirm reset">
                <p>Reset every ticket, payment and draft to the original shop data?</p>
                <button type="button" className="btn btn-decline" disabled={busy} onClick={reset}>
                  {busy ? "Resetting…" : "Yes, reset"}
                </button>
                <button type="button" className="link" onClick={() => setConfirmReset(false)}>Cancel</button>
              </div>
            )}
            {runBusy && <p className="hint">Reset is available once the current run finishes.</p>}
            {error && <p className="error" role="alert">{error}</p>}
          </div>
        </>
      )}
    </section>
  );
}
