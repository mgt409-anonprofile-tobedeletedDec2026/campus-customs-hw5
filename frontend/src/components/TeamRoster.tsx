import { AGENT_ORDER, CHARACTERS } from "../characters";
import { awardDundies } from "../office";
import type { AgentEvent, AgentId } from "../types";
import { Avatar } from "./Avatar";

interface AgentWork {
  involved: boolean;
  summary: string | null;
  tools: string[];
  handedOffByTeammate: boolean;
  steps: number;
}

function summarize(events: AgentEvent[]): Record<AgentId, AgentWork> {
  const work = {} as Record<AgentId, AgentWork>;
  for (const a of AGENT_ORDER) {
    work[a] = { involved: false, summary: null, tools: [], handedOffByTeammate: false, steps: 0 };
  }
  for (const e of events) {
    const a = e.agent as AgentId | null;
    if (e.event === "delegation" && e.to) {
      work[e.to].involved = true;
      if (a && a !== "boss") work[e.to].handedOffByTeammate = true;
    }
    if (!a || !work[a]) continue;
    if (e.event === "agent_start") work[a].involved = true;
    if (e.event === "tool_call" && e.tool && e.tool !== "final_result") {
      work[a].steps += 1;
      if (e.tool !== "ask_teammate" && !work[a].tools.includes(e.tool)) work[a].tools.push(e.tool);
    }
    if (e.event === "agent_end" && e.said) work[a].summary = e.said;
  }
  return work;
}

// Who did what on this ticket, and the Dundie each one earned (shown once the run is done).
export function TeamRoster({ events, finished }: { events: AgentEvent[]; finished: boolean }) {
  const work = summarize(events);
  // "Fastest Worker" goes to one agent only: the first with the fewest steps.
  const contenders = AGENT_ORDER.filter((a) => a !== "boss" && work[a].involved && work[a].summary);
  const fastest = contenders.length > 1
    ? contenders.reduce((best, a) => (work[a].steps < work[best].steps ? a : best))
    : null;
  const runId = events[0]?.run_id ?? "none";
  const dundies = awardDundies(runId, Object.fromEntries(AGENT_ORDER.map((a) => [a, {
    involved: work[a].involved,
    handedOffByTeammate: work[a].handedOffByTeammate,
    isFastest: a === fastest,
  }])) as Record<AgentId, { involved: boolean; handedOffByTeammate: boolean; isFastest: boolean }>);

  return (
    <section className="panel roster" aria-labelledby="roster-title">
      <h2 id="roster-title">👥 What each agent did</h2>
      <div className="roster-grid">
        {AGENT_ORDER.map((a) => {
          const who = CHARACTERS[a];
          const w = work[a];
          const dundie = dundies[a];
          return (
            <article key={a} className={`agent-card ${w.involved ? "" : "idle"}`} style={{ borderTopColor: who.color }}>
              <header>
                <Avatar who={who} size={50} />
                <div>
                  <h3 style={{ color: who.ink }}>{who.name}</h3>
                  <p className="role">{who.emoji} {who.role}</p>
                </div>
              </header>
              <p className="agent-summary">
                {w.summary ?? (w.involved ? "Working on it…" : events.length ? "Not needed on this ticket." : "Waiting for a ticket.")}
              </p>
              {w.tools.length > 0 && (
                <p className="agent-tools">
                  {w.tools.map((t) => <code key={t}>{t}</code>)}
                </p>
              )}
              {finished && events.length > 0 && (
                <p className="dundie-chip" title={dundie.blurb}>🏆 {dundie.title}</p>
              )}
            </article>
          );
        })}
      </div>

      {finished && events.length > 0 && (
        <div className="tv" role="group" aria-labelledby="dundies-title">
          <div className="tv-screen">
            <h3 id="dundies-title">📺 The Dundies · live from Chili's</h3>
            <ul className="dundie-list">
              {AGENT_ORDER.map((a) => {
                const d = dundies[a];
                return (
                  <li key={a}>
                    <span className="dundie-trophy" aria-hidden="true">🏆</span>
                    <div>
                      <b>{d.emoji} {d.title}</b>
                      <span>{CHARACTERS[a].name}: {d.blurb}</span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
          <div className="tv-knobs" aria-hidden="true"><span /><span /></div>
        </div>
      )}
    </section>
  );
}
