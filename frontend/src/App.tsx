import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, session } from "./api";
import { CashCounter } from "./components/CashCounter";
import { DavidDesk } from "./components/DavidDesk";
import { LiveFeed } from "./components/LiveFeed";
import { MichaelJokes } from "./components/MichaelJokes";
import { TeamRoster } from "./components/TeamRoster";
import { TicketBoard } from "./components/TicketBoard";
import { LOADING_LINES } from "./office";
import type { AgentEvent, CashResponse, PaymentRequest, RunStatus, Ticket } from "./types";

const POLL_RUNNING_MS = 1500;
const POLL_IDLE_MS = 5000;

// Only the latest run of a ticket is shown in the feed and the roster.
function latestRun(events: AgentEvent[]): AgentEvent[] {
  let start = -1;
  events.forEach((e, i) => { if (e.event === "run_start") start = i; });
  if (start === -1) return [];
  const runId = events[start].run_id;
  return events.slice(start).filter((e) => e.run_id === runId);
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [today, setToday] = useState<string>("");
  const [selected, setSelected] = useState<number | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [run, setRun] = useState<RunStatus | null>(null);
  const [cash, setCash] = useState<CashResponse>({ checking_balance: null, as_of: null });
  const [requests, setRequests] = useState<PaymentRequest[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);
  const lastIndex = useRef(-1);
  const running = run?.running ?? false;

  const refresh = useCallback(async () => {
    try {
      const [board, r, c] = await Promise.all([api.tickets(), api.currentRun(), api.cash()]);
      setTickets(board.tickets);
      setToday(board.today);
      setRun(r);
      setCash(c);
      if (loggedIn) setRequests((await api.paymentRequests("pending")).requests);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [loggedIn]);

  // Poll the board, run status and cash: fast while the team works, slow otherwise.
  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, running ? POLL_RUNNING_MS : POLL_IDLE_MS);
    return () => clearInterval(timer);
  }, [refresh, running]);

  // Load the selected ticket's events, then keep appending new ones.
  useEffect(() => {
    if (selected === null) return;
    let cancelled = false;
    lastIndex.current = -1;
    setEvents([]);
    const pull = async () => {
      try {
        const res = await api.events(selected, lastIndex.current);
        if (cancelled || res.events.length === 0) return;
        lastIndex.current = res.events[res.events.length - 1].index;
        setEvents((prev) => [...prev, ...res.events]);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    };
    pull();
    const timer = setInterval(pull, running ? POLL_RUNNING_MS : POLL_IDLE_MS);
    return () => { cancelled = true; clearInterval(timer); };
  }, [selected, running]);

  // Restore David's session after a page refresh.
  useEffect(() => {
    if (!session.get()) return;
    api.session().then((s) => { if (s.logged_in) setLoggedIn(true); else session.clear(); }).catch(() => {});
  }, []);

  // Easter egg: type "beets" anywhere.
  useEffect(() => {
    let typed = "";
    const onKey = (e: KeyboardEvent) => {
      typed = (typed + e.key.toLowerCase()).slice(-5);
      if (typed === "beets") setToast("🐻 Bears. 🥕 Beets. 🚀 Battlestar Galactica. — Dwight");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(t);
  }, [toast]);

  const runEvents = useMemo(() => latestRun(events), [events]);
  const selectedTicket = tickets.find((t) => t.id === selected) ?? null;
  const runningThis = running && run?.ticket_id === selected;
  const finished = !runningThis && runEvents.some((e) => e.event === "run_end");

  async function startRun(id: number) {
    setSelected(id);
    try {
      await api.runTicket(id);
      setToast(`☕ Michael: "Ticket #${id}? I'll get my best people on it. Also me."`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function login(password: string) {
    const res = await api.login(password);
    session.set(res.token);
    setLoggedIn(true);
    setRequests((await api.paymentRequests("pending")).requests);
  }

  async function logout() {
    await api.logout().catch(() => {});
    session.clear();
    setLoggedIn(false);
    setRequests([]);
  }

  async function reset() {
    await api.reset();
    setSelected(null);
    setEvents([]);
    setToast("🔥 Fire drill complete. Everything is back to the original shop data.");
    await refresh();
  }

  return (
    <div className="desk">
      <header className="masthead">
        <button
          type="button"
          className="mug"
          aria-label="World's Best Boss mug"
          onClick={() => setToast("☕ \"I'm not superstitious, but I am a little stitious.\" — Michael")}
        >
          WORLD'S<br />BEST<br />BOSS
        </button>
        <div className="brand">
          <h1>Campus Customs <span>Agent Desk</span></h1>
          <p>New Haven Branch · "Limitless paper in a paperless world" · Shop date <strong>{today || "…"}</strong></p>
        </div>
        <CashCounter balance={cash.checking_balance} asOf={cash.as_of} />
      </header>

      {toast && <div className="toast" role="status">{toast}</div>}
      {error && (
        <div className="banner-error" role="alert">
          ⚠️ {error} <button type="button" className="link" onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      {loading && <p className="loading">{LOADING_LINES[Math.floor(Date.now() / 1000) % LOADING_LINES.length]}</p>}

      <main className="layout">
        <TicketBoard
          tickets={tickets}
          selected={selected}
          runningTicket={running ? run?.ticket_id ?? null : null}
          onSelect={setSelected}
          onRun={startRun}
          busy={running}
        />

        <div className="center">
          <MichaelJokes active={runningThis} />
          <LiveFeed events={runEvents} running={runningThis} ticketId={selected} />
          {selectedTicket && runEvents.length > 0 && (
            <TeamRoster events={runEvents} finished={finished} />
          )}
        </div>

        <DavidDesk
          loggedIn={loggedIn}
          requests={requests}
          onLogin={login}
          onLogout={logout}
          onDecided={refresh}
          onReset={reset}
          runBusy={running}
        />
      </main>

      <footer className="footer">
        <span>Campus Customs Multi-Agent Operations · every agent runs on gpt-6-luna · no emails ever leave this office</span>
        <span className="eggs">
          <button type="button" className="egg" onClick={() => setToast("🌶️ Kevin's Famous Chili hit the carpet. Again. Oscar is not letting him near the books.")}>
            🌶️ Kevin's chili
          </button>
          <button type="button" className="egg" onClick={() => setToast("📎 Dwight: \"My stapler is in Jell-O again. PAM!\" Pam: \"No idea what you're talking about.\"")}>
            📎 Where's my stapler?
          </button>
          <button type="button" className="egg" onClick={() => setToast("🥨 It's Pretzel Day! The free pretzel guy is here. Best day of the year.")}>
            🥨 Pretzel Day
          </button>
        </span>
      </footer>
    </div>
  );
}
