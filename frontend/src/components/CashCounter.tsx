import { useEffect, useRef, useState } from "react";

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

// The checking balance. When it drops, a red "-$X" pops off and the number counts down.
export function CashCounter({ balance, asOf }: { balance: number | null; asOf: string | null }) {
  const [shown, setShown] = useState<number | null>(balance);
  const [pop, setPop] = useState<{ key: number; amount: number } | null>(null);
  const prev = useRef<number | null>(balance);

  useEffect(() => {
    if (balance === null) return;
    const from = prev.current;
    prev.current = balance;
    if (from === null || from === balance) {
      setShown(balance);
      return;
    }
    if (balance < from) setPop({ key: Date.now(), amount: from - balance });
    const start = performance.now();
    const duration = 1400;
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(from + (balance - from) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [balance]);

  useEffect(() => {
    if (!pop) return;
    const timer = setTimeout(() => setPop(null), 2600);
    return () => clearTimeout(timer);
  }, [pop]);

  return (
    <section className="cash" aria-label="Checking balance">
      <div className="cash-label">💵 Checking balance</div>
      <div className="cash-amount" aria-live="polite">
        {shown === null ? "…" : money(shown)}
        {pop && (
          <span key={pop.key} className="cash-pop" aria-hidden="true">
            −{money(pop.amount)}
          </span>
        )}
      </div>
      <div className="cash-note">
        {asOf ? `as of shop date ${asOf}` : "loading"} · cash only goes out
      </div>
    </section>
  );
}
