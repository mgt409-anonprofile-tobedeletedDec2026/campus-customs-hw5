import { useEffect, useState } from "react";
import { CHARACTERS } from "../characters";
import { IGNORED_BY, MICHAEL_LINES } from "../office";
import { Avatar } from "./Avatar";

// While the team works, Michael wanders by with a joke every few seconds.
export function MichaelJokes({ active }: { active: boolean }) {
  const [i, setI] = useState(() => Math.floor(Math.random() * MICHAEL_LINES.length));

  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setI((n) => n + 1), 7000);
    return () => clearInterval(timer);
  }, [active]);

  if (!active) return null;
  return (
    <aside className="michael-jokes" aria-live="off" aria-label="Michael's commentary (just for fun)">
      <Avatar who={CHARACTERS.boss} size={52} />
      <div>
        <p className="joke">“{MICHAEL_LINES[i % MICHAEL_LINES.length]}”</p>
        <p className="ignored">{IGNORED_BY[i % IGNORED_BY.length]}</p>
      </div>
    </aside>
  );
}
