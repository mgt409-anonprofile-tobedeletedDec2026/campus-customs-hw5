# Campus Customs Agent Desk: Design Notes

The dashboard (`frontend/`, React + Vite + TypeScript) is meant to feel like sitting at a desk in the Dunder Mifflin office, not like a tech console. People should *want* to watch Michael's team work. It still has to be crystal clear about the serious part: only David Wallace can move money.

## Look and feel: bright office, not a dark console
- **Palette:** office-wall blue with a faint ceiling-tile grid, white "paper" cards, yellow sticky notes, and lots of hot pink. It matches `desk_tickets.html`. I asked for no black backgrounds because a dark theme felt too serious for an Office joke.
- **Type:** a clean sans-serif for anything you need to read (amounts, statuses, summaries). A handwritten font only for jokes and margin notes, so the fun never gets in the way of the facts.
- **Physical desk details:** tickets are tilted sticky notes held on with pink tape. Buttons have a chunky "pressed" shadow. The masthead has the **World's Best Boss** mug, and clicking it gets you a Michael quote.

## Layout: three zones, left to right like the work itself
| Left | Center | Right |
|---|---|---|
| **Ticket board:** three sticky notes, each with a "Start the team" button | **The office:** Michael's jokes, then the live feed, then "What each agent did" and the Dundies | **David Wallace's desk:** login, approval inbox, reset |

The **checking balance** sits in the top-right corner of the masthead on its own yellow sticky note, so it's always visible no matter what you're doing. On smaller screens the columns stack (board → office → David's desk), and the cash note moves under the title.

## How each agent reads differently
Every character has their own **color, cartoon portrait, emoji, and voice**, based on how they look in the show, so you can tell them apart at a glance:

| Agent | Color | Portrait cues | Emoji |
|---|---|---|---|
| Michael Scott (Boss) | Dunder Mifflin blue | Side-parted dark hair, navy suit, red tie | ☕ |
| Dwight Schrute (Inventory) | Mustard yellow | Bowl haircut, glasses, mustard short-sleeve shirt, brown tie | 🐻 |
| Oscar Martinez (Accounting) | Green | Short dark hair, goatee, green shirt | 🧮 |
| Darryl Philbin (Facilities) | Purple | Buzz cut, goatee, work shirt with a safety-orange collar | 🔧 |
| Pam Beesly (Customer Service) | Pink | Long auburn curly hair, pink cardigan | 🎨 |
| David Wallace (human approver) | Navy | Silver hair, charcoal suit, blue tie | 🖊️ |

In the **live feed**:
- **Speech bubbles** in each agent's color show what they say (their personality comes from their prompt, e.g. Oscar starts with "Actually…").
- **Hand-off banners** make delegation obvious: **Michael → Dwight**, with the actual request underneath.
- **Tool chips** show what each agent is *doing* in plain English ("Dwight checks stock & vendors") with the real MCP tool name next to it.
- A red **LIVE** dot pulses while the team works. The feed refreshes itself every 1.5 seconds and scrolls to the newest line.

## How resolved tickets show up
Each sticky note wears status **stickers**:
- 📬 **Open**: nobody has worked it yet.
- ⏳ **Team working…**: pulsing pink while the run is in progress.
- ✅ **Resolved**: the moment the team's run finishes, the backend marks the ticket resolved.
- 💰 **Awaiting David · $840**: a separate, slightly crooked yellow sticker if a payment request on that ticket still needs approval.

I kept "Resolved" and "Awaiting David" as **two separate stickers** on purpose. The agents' work is done, but the money decision stays with the human. You can see both facts at once.

## How cash shows up
- The balance is big, green, and always on screen.
- When David approves a payment, a **red "−$840.00" pops off** the balance and floats away while the number **counts down** to the new total. It feels like money actually leaving the register.
- If a payment would overdraw cash, it never happens. Instead **Oscar appears in a green speech bubble** inside David's inbox with his refusal: *"Actually, I have to refuse… We are $80.00 short, and the balance can never go negative. No money moved."*

## David Wallace's desk (the serious part)
- **Login required.** The password box is the only thing visible until David logs in. The backend checks a salted hash and locks out repeated wrong guesses.
- **Approval inbox:** each request card shows who asked (usually Oscar), why, the amount, and a **"David's reason" box**. The reason is saved with the approval or decline.
- **Reset database (fire drill)** also requires login, asks "Are you sure?" first, and is disabled while a run is in progress.
- A one-line reminder under the login: *"Agents can prepare payments, but only David can approve them."*

## Creative touches (all built in, zero AI tokens)
- **Michael's running commentary:** while the team works, Michael wanders into a dashed "thought bubble" every 7 seconds with a joke, often poking fun at his own team ("Oscar says 'actually' so much I'm going to start charging him a dollar. Then we'd have revenue!"). A little italic line underneath confirms the agents are ignoring him: *"Dwight keeps typing."* / *"Oscar does not look up."*
- **The Dundies, on a TV:** when a run finishes, a wood-paneled retro TV ("📺 The Dundies · live from Chili's") hands every agent an award. There are **23 Dundies**, drawn fresh for each run, so two runs rarely look the same. The draw is seeded by the run's ID, so a given run always shows the same awards when you come back to it, and no two agents share an award in one run.
  - **Each character's own Dundies:**
    - Michael: World's Best Boss, Dundies Host Extraordinaire, Kind of a Big Deal, Improv Class Valedictorian
    - Dwight: Assistant (to the) Regional Manager of the Year, Beet Farmer of the Year, Schrute Bucks Millionaire, Volunteer Sheriff's Deputy
    - Oscar: Show Me the Money, The "Actually…" Award, Finer Things Club President, Keeper of the Books (Not Kevin)
    - Darryl: Busiest Beaver, Warehouse Wisdom, Best Keyboard Jam Session
    - Pam: Whitest Sneakers, **Head of the Party Planning Committee**, Best Watercolor of the Building, Reigning Prank Champion
  - **Earned awards** (more likely when deserved): **Fastest Worker** (the helper with the fewest steps) and **Stamford Transfer** (handed the job mid-ticket by a teammate)
  - **Wildcards** any helper can win: **Temp to VP** (very Ryan of you) and **Yale's Finest** ("Went to Yale. Ever heard of it? Boola Boola!", our New Haven spin on Andy Bernard's Cornell)
  - **For agents the ticket didn't need:** Lazy Scranton Award, The Toby Flenderson Award ("Was technically here. Nobody noticed."), Pretzel Day Champion
- **Easter eggs:**
  - Type **"beets"** anywhere: *Bears. Beets. Battlestar Galactica.*
  - Footer buttons: **🌶️ Kevin's chili** (the chili incident), **📎 Where's my stapler?** (Jell-O prank), **🥨 Pretzel Day**
  - Loading lines like "Asking Toby to leave the room…"
  - Starting a run: Michael says *"I'll get my best people on it. Also me."*

## Accessibility and clarity
- Dark navy text on light backgrounds for strong contrast. Every button and input has a label, and focus outlines are visible.
- Live regions announce new feed lines and the balance. Michael's jokes are **not** announced, so they don't interrupt screen readers.
- Clear loading text, error banners (e.g. "Can't reach the backend… is uvicorn running?"), and inline errors on the login and approval forms.
- Animations switch off for people who set "reduce motion."

## How it connects
The page only talks to the FastAPI backend at `http://localhost:8000` (routes in `harness.md`, section 9). The backend allows the Vite page at `http://localhost:5173`. Start it with `npm run dev` in `frontend/`.
