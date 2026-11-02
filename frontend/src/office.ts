// Built-in Office fun. Nothing here calls the AI, so it costs no tokens.
import type { AgentId } from "./types";

// Michael "helps" while the team works. The agents ignore him.
export const MICHAEL_LINES: string[] = [
  "Would I rather be feared or loved? Easy. Both. I want people to be afraid of how much they love me.",
  "Dwight, you're checking stock by SKU *and* size? That's... actually really smart. Don't tell him I said that.",
  "Oscar says 'actually' so much I'm going to start charging him a dollar. Then we'd have revenue!",
  "I'm not superstitious, but I am a little stitious. Knock on wood that cash stays positive.",
  "Darryl, can you teach me that calm thing you do? No? Okay. Cool. Cool cool cool.",
  "Pam, put a doodle on that draft. A big one. Of me. Holding a Dundie.",
  "Sometimes I'll start a sentence and I don't even know where it's going. I just hope I find it along the way. Like this ticket.",
  "An unpaid invoice is like a parking ticket for your soul.",
  "I declare... a very orderly approval process! (Oscar told me I'm not allowed to declare bankruptcy.)",
  "Dwight just said 'bears' under his breath. I'm choosing not to ask.",
  "Fun fact: I wanted to give the hoodies away for free. Oscar made a face. So, no.",
  "Is anybody listening to me? ...Great, nobody. Productive team!",
  "The rent is due in two days. That's what she sa— no. Not today. David Wallace might be watching.",
  "Oscar, if cash goes negative, does that mean we have *anti-money*? Like a black hole? Cool.",
  "I learned management from the best: me.",
  "Pam's drafts are so nice I almost want to send them. But I can't. Rules. Sad face.",
  "Dwight, stop sharpening that pencil. It's a ticket board, not a bear attack.",
  "You miss 100% of the shots you don't take. – Wayne Gretzky. – Michael Scott.",
];

export const IGNORED_BY = [
  "Dwight keeps typing.",
  "Oscar does not look up.",
  "Darryl puts in one earbud.",
  "Pam smiles politely and keeps drafting.",
  "Nobody looks up.",
];

export interface Dundie {
  title: string;
  blurb: string;
  emoji: string;
}

// Each character's own Dundies, for a job well done. One is picked per run.
const SIGNATURE: Record<AgentId, Dundie[]> = {
  boss: [
    { title: "World's Best Boss", blurb: "Delegated like a legend. Paid nothing himself.", emoji: "☕" },
    { title: "Dundies Host Extraordinaire", blurb: "Gave a speech nobody asked for. Nailed it anyway.", emoji: "🎤" },
    { title: "Kind of a Big Deal", blurb: "Leather-bound tickets. Smells of rich mahogany.", emoji: "📚" },
    { title: "Improv Class Valedictorian", blurb: "Pulled out a fake gun zero times. Growth!", emoji: "🎭" },
  ],
  inventory: [
    { title: "Assistant (to the) Regional Manager of the Year", blurb: "Counted every size. Feared no bear.", emoji: "🐻" },
    { title: "Beet Farmer of the Year", blurb: "Stock counted with Schrute Farms precision.", emoji: "🌱" },
    { title: "Schrute Bucks Millionaire", blurb: "Paid in Schrute Bucks. Worth exactly nothing. Proud anyway.", emoji: "💵" },
    { title: "Volunteer Sheriff's Deputy", blurb: "Policed every SKU and size. No vendor got past him.", emoji: "⭐" },
  ],
  accounting: [
    { title: "Show Me the Money Award", blurb: "Kept cash positive. Said 'actually' at least once.", emoji: "🧮" },
    { title: "The 'Actually…' Award", blurb: "Corrected someone. Was right. Again.", emoji: "☝️" },
    { title: "Finer Things Club President", blurb: "Balanced the books with a cup of Earl Grey.", emoji: "🫖" },
    { title: "Keeper of the Books (Not Kevin)", blurb: "No 'keleven.' No chili on the ledger.", emoji: "📒" },
  ],
  facilities: [
    { title: "Busiest Beaver", blurb: "Kept the lights on and the landlord calm.", emoji: "🔧" },
    { title: "Warehouse Wisdom Award", blurb: "Said one calm sentence. Fixed everything.", emoji: "📦" },
    { title: "Best Keyboard Jam Session", blurb: "Rent handled. 'Little Kid Lover' still in his head.", emoji: "🎹" },
  ],
  customer_service: [
    { title: "Whitest Sneakers", blurb: "Drafts so kind they glow. None were sent.", emoji: "👟" },
    { title: "Head of the Party Planning Committee", blurb: "Ran the drafts like a PPC meeting. Streamers optional.", emoji: "🎉" },
    { title: "Best Watercolor of the Building", blurb: "Every draft a tiny work of art. Hung in the break room.", emoji: "🎨" },
    { title: "Reigning Prank Champion", blurb: "Dwight's stapler is still in Jell-O. Allegedly.", emoji: "📎" },
  ],
};

// Awards any helper can win, depending on how they worked.
export const FASTEST_WORKER: Dundie = { title: "Fastest Worker", blurb: "In, done, out. Fewest steps on the team.", emoji: "⚡" };
export const STAMFORD_TRANSFER: Dundie = {
  title: "Stamford Transfer", blurb: "Got handed this mid-ticket by a teammate and made it work.", emoji: "🚚",
};
const WILDCARDS: Dundie[] = [
  { title: "Temp to VP", blurb: "Started as 'the help.' Ended running the ticket. Very Ryan of you.", emoji: "📈" },
  { title: "Yale's Finest", blurb: "Went to Yale. Ever heard of it? Brings it up constantly. Boola Boola!", emoji: "🐶" },
];

// For anyone the ticket didn't need.
const IDLE: Dundie[] = [
  { title: "Lazy Scranton Award", blurb: "Not needed on this ticket. Enjoyed a pretzel instead.", emoji: "🥨" },
  { title: "The Toby Flenderson Award", blurb: "Was technically here. Nobody noticed.", emoji: "🫥" },
  { title: "Pretzel Day Champion", blurb: "Skipped the ticket. Got two pretzels. Zero regrets.", emoji: "🥨" },
];

// Same run → same Dundies (so they don't flicker); a new run → a fresh draw.
function seeded(seed: string): () => number {
  let h = 2166136261;
  for (const ch of seed) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return ((h ^= h >>> 16) >>> 0) / 4294967296;
  };
}

function shuffled<T>(items: T[], rand: () => number): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export interface AgentRunFacts {
  involved: boolean;
  handedOffByTeammate: boolean;
  isFastest: boolean;
}

// Hand out one Dundie per agent for a run, with no repeats (except for idle awards).
export function awardDundies(runId: string, facts: Record<AgentId, AgentRunFacts>): Record<AgentId, Dundie> {
  const rand = seeded(runId);
  const used = new Set<string>();
  const awards = {} as Record<AgentId, Dundie>;
  for (const agent of Object.keys(facts) as AgentId[]) {
    const f = facts[agent];
    if (!f.involved) {
      awards[agent] = IDLE[Math.floor(rand() * IDLE.length)];
      continue;
    }
    // Earned awards get extra tickets in the hat, so they show up often but not always.
    const hat = [...SIGNATURE[agent], ...SIGNATURE[agent]];
    if (agent !== "boss") {
      if (f.handedOffByTeammate) hat.push(STAMFORD_TRANSFER, STAMFORD_TRANSFER, STAMFORD_TRANSFER);
      if (f.isFastest) hat.push(FASTEST_WORKER, FASTEST_WORKER, FASTEST_WORKER);
      hat.push(...WILDCARDS);
    }
    const pick = shuffled(hat, rand).find((d) => !used.has(d.title)) ?? SIGNATURE[agent][0];
    used.add(pick.title);
    awards[agent] = pick;
  }
  return awards;
}

export const LOADING_LINES = [
  "Sharpening pencils…",
  "Locating the stapler (check the Jell-O)…",
  "Asking Toby to leave the room…",
  "Warming up Kevin's famous chili…",
];
