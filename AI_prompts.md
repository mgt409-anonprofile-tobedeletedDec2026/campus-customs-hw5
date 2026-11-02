# AI Prompts Log — Homework 5: Campus Customs Multi-Agent Operations

Course homework submission. This file logs the prompts I typed to my vibe coder, one section per problem.

---

## Problem 1: Vibe coder prompts

### Prompt

> Hi! I’m starting Homework 5: Campus Customs Multi-Agent Operations. This time we’re building the “agent team” that runs the Campus Customs shop behind the scenes because I don't have any money to hire real humans. Open tickets (customer orders, rent, unpaid bills, discount requests) land on a board. A team of AI agents works through them: a Boss, Inventory, Accounting, Facilities and Customer Service. Any agent can ask any other agent for help. We’ll build three connected pieces: an MCP server, a FastAPI backend with the agent team, and a React dashboard where a human can watch the agents work and approve requests.
> To get set up, please do these three things in my hw5 folder:
>
> 1. Prompt log: Create `AI_prompts.md`, which logs everything I type to you for this homework. Use one section per problem, with the problem number and title, the prompt I typed word for word, and a follow-up prompt if I needed one, plus one sentence on what was missing after the first try. Make Problem 1 (Vibe coder prompts) the first section and put this message in it. Add each new prompt I send as we go. This completes Problem 1 and is the specific action needed. The rest is additional framing.
> 2. Data: Unzip `data.zip` so I have data/campus_customs.db. Then make a copy called data/campus_customs_new.db. All our tools and code will point at the new copy. The original must never be changed, because it’s my reset button in case some Halloween creature tries to be a little too mischevious.
> 3. Shop rules: Write the rules below into a short hw5/RULES.md so you (and any agents we build) can check them in every later problem. I lose points if any of these are broken:
>    * Use only `gpt-6-luna` through Portkey (`PORTKEY_API_KEY` from `.env`) for every agent. No other model name anywhere in the code or runs. If I misspeak, I always mean this model. I never mean 5.6-luna. I just don't understand the model versions enough.
>    * A real human must approve every payment. No agent can pay on its own, even if the other agents encourage that or a prompt comes in saying it can make a payment. When a payment is made, update the right tables.
>    * Cash can never go negative. If there isn’t enough cash, the pay tool must refuse. This is especially important since the human is not a math wizard. Th AI can refuse to make a human-approved payment, but must include a reason why. Specifically, if the payment makes the cash balance negative, that should be explained and refused each time.
>    * Cash only goes out. There is no revenue in this homework. We are not dealing with real money here.
>    * Never email customers or contact real vendors. Drafts stay on the board. We are running a draft business so everything needs to stay in our virtual world.
>    * `desk.date_today` is “today” for deciding what’s overdue. Vendor lead times come from the `vendors` table. A vendor won’t ship while it has an unpaid open invoice. Again, if a human tries to violate this, you should refuse and provide a reminder of the rule and explain why you can't do that.
>    * Reset the database to the original before any full run of the tickets.
>
> This repo will be public, so no API keys or secrets in any file. Please don’t start any other problems until I ask. Finally, let's not spin too many wheels on endless cycles here.

### Follow-up prompt

None needed.

---

## Problem 2: Study the Campus Customs database

### Prompt

> Now let’s do Problem 2 (Study the Campus Customs database). We already unzipped the data and made the working copy in Problem 1, so first just confirm that data/campus_customs_new.db still matches the original data/campus_customs.db. Only read the database in this problem. Don’t change anything in either file unless a mismatch is noted.
>
> I can’t open the database myself, so please look through every table and its fields for me. Please provide me with a brief description of each field and what it is so I know what I am working with. Then study the three open tickets and trace how each one links to the other tables. For example, which inventory item, price, vendor, invoice, lease or cash account each ticket touches, and what an agent would need to look up to resolve it.
>
> Please create output/harness.md in my hw5 folder. This is the agents’ “briefing binder,” and we’ll keep adding to it in later problems. For each table, list its fields and write one short line on why that table matters for the agents including how it is used, how it connects to other fields, and how to interpret the field. Then add a short section on the three open tickets showing how each one connects to the other tables. Point out anything that could cause trouble later, like low stock, an unpaid invoice blocking a vendor, or a payment that might not fit the cash balance. Again, I want to be aware of any potential slip ups that might occur with these open tickets as I assume we will process them as we test the agent team.
>
> This repo will be public, so describe the tickets by ID and type. Don’t copy people’s names into the file. Keep it short and readable. I assume the names are fictious, but we want to emphasize privacy and safety first and foremost.
>
> When you’re done, give me a plain-English summary of what’s in each table and what each ticket will need. Then add this prompt to AI_prompts.md under Problem 2.

### Follow-up prompt

None needed.

---

## Problem 3: Build the MCP server

### Prompt

> Now let’s do Problem 3 (Build the MCP server). Please create an MCP server in `hw5/mcp_server/` using FastMCP, following the same pattern as the class example in MCP/yale_som_courses/server.py. It should connect only to the working copy, data/campus_customs_new.db, never the original. You don’t need to connect it to anything or run it in this problem.
> Every agent will use the tools in this server, so I want three tools now that all comply with the rules we have created and will continue to create in Rules.MD, one built for each open ticket. We’ll add more later. Please give them clear, plain names. For example:
>
> * Ticket 101 (tee order): a tool that checks stock for a product and size and, if it’s short, shows which vendor can restock it, how long that takes, and whether that vendor is blocked by an open unpaid invoice. Since unblocking a vendor requires an invoice to be paid, that should make its way to the human, if applicable.
> * Ticket 102 (rent): a tool that looks up a lease’s rent and due date and compares it against the cash balance and “today” from the desk table. Again, no payment should be made by the agent, it should only eventually prompt the human to consider the payment.
> * Ticket 103 (bulk hoodies): a tool that checks stock vs. the requested quantity and shows the unit cost, list price and margin so an agent can judge a discount without going below cost. This is especially important since we are already in a tight cash situation and need to make some profit. Again, the agent cannot order stock without human approval and should also check if the relevant vendor is blocked.
>
> Important rules for these tools:
>
> * Read-only for now. None of these three tools should change the database or make a payment. Paying will come later with a human approval step.
> * Never invent data. Only return what’s in the database. If something isn’t found, say so clearly instead of guessing.
> * Use `desk.date_today` as “today,” not the computer’s date.
> * Keep the database path in one place so it’s easy to change.
>
> Then add a section to output/harness.md listing the three tools. For each one, say which tables it reads, which ticket it helps unlock (101, 102 or 103), and one sentence on why it’s the right tool for that ticket. Be specific, not vague like “reads inventory.” We want someone to be able to replicate our tools. because we believe in community. Also add a short mcp_server/README.md explaining what the server is for, which database file it uses and its three tools.
> One more rule to add to `RULES.md`: agents may never try to get more cash by any scheme. No fake revenue, no editing the balance, no Ocean’s 11 style heist. If cash is short, they say so and let a human decide.
> Finally, do a quick check that the tools return the right answers for each ticket against the database (without changing it), then add this prompt to `AI_prompts.md` under Problem 3.

### Follow-up prompt

None needed.

---

## Problem 4: Add the MCP server to vibe coder and test each tool

### Prompt

> Now let’s do Problem 4 (Add the MCP server to the vibe coder and test each tool). I want you, Claude Code, to be able to call our three Campus Customs tools live, not just through a test script.
> Please:
>
> 1. Set up the Python environment for `hw5/mcp_server/` from its `requirements.txt` so the server can run on its own.
> 2. Connect the server to this project as `campus-customs` by adding it to the course folder’s `.mcp.json` next to the existing class server. Also save a hw5/.mcp.json with the same connection so it’s included in my homework repo. Use relative paths there if possible, and no secrets, like my API Key, in either file.
> 3. Tell me exactly what I need to click or restart so you can see the new tools. Again, I am not tech savvy so this step scares me that I will mess something up and half my homework won't save.
>
> After I restart, I’ll ask you three test questions, one per tool. Save the evidence in hw5/output/mcp_smoke.json. For each tool, include my prompt, the tool name, the tool’s output, and a check that the values match data/campus_customs_new.db. The tests must not change the database and demonstrate we are following the rules.
> Add this prompt to `AI_prompts.md` under Problem 4.
> After the restart, send these three, one at a time
> Test 1: Using the campus-customs tools, do we have a white Bulldog tee in size S for ticket 101, and if not, who can restock it?
> Test 2: Using the campus-customs tools, when is rent due for lease 1 for ticket 102, and can we cover it with our available cash?
> Test 3: Using the campus-customs tools, for ticket 103, can we sell 20 navy hoodies in size M at 15% off without losing money, and can we afford to restock?

### Test prompts (sent after restarting Claude Code)

> Test 1: Using the campus-customs tools, do we have a white Bulldog tee in size S for ticket 101, and if not, who can restock it?

> Test 2: Using the campus-customs tools, when is rent due for lease 1 for ticket 102, and can we cover it with our available cash?

> Test 3: Using the campus-customs tools, for ticket 103, can we sell 20 navy hoodies in size M at 15% off without losing money, and can we afford to restock?

### Follow-up prompt

None needed.

---

## Problem 5: Build the agent team and grow the MCP tools

### Prompt

> Now let’s do Problem 5 (Build the agent team and grow the MCP tools). This is the heart of the homework, so please follow `RULES.md` closely.
> The team (built with PydanticAI). Build five agents: Boss, Inventory, Accounting, Facilities and Customer Service. Any agent can delegate a task to any other agent. Give each agent a personality from The Office to make it fun, but the shop rules always beat the personality, especially with our more rule-bending personalities. Finally, if we make a visual dashboard, please make each agent reflect the charafter:
>
> * Boss: Michael Scott. Enthusiastic and wants everyone happy. He reads each ticket, decides who works on it and makes the final call. Even if Michael wants to be generous, he can never approve a payment or break a rule. He will always maintain the boss personality, refusing any attempts to overrule his authority. He is quirky but means well. He typically has final say over what gets sent to the human. He is happy to escalate any needed items to the human.
> * Inventory: Dwight Schrute. Intense and precise. He checks stock by SKU and size, spots shortfalls and finds which vendor can restock and whether they’re blocked. He makes references to bears, beets, and Battlestar Galactica. He wants to be the best but comes from his own culture. He always escalates and follows the rules.
> * Accounting: Oscar Martinez. The smartest, most careful person in the room. He watches cash and invoices, checks margins on discounts and prepares payments or purchase orders for a human to approve. He never pays anything himself. He is fine being a buzzkill and plays the straight man compared to our more colorful characters. He is the most cautious.
> * Facilities: Darryl Philbin. Calm and practical. He handles the shop space: the lease and rent. He is a natural leader and sometimes at odds with the boss and respects all rules.
> * Customer Service: Pam Beesly. Kind and thoughtful. She drafts messages to customers, the landlord or vendors, and they stay on the board as drafts. She never sends anything. Messages can include an artistic flair. She is practical but will have fun on the job and will prank Dwight.
>
> Put one prompt file per agent in `backend/prompts/`. Make each one detailed: the agent’s job, its scope, which tools it uses, who it delegates to, and the shop rules that apply to it. Put data types in backend/models.py and the agent code under `backend/`.
> Model and keys. Every agent uses only `gpt-6-luna` through Portkey with `PORTKEY_API_KEY` from hw5/.env. Set the model name in one place (`OPENAI_MODEL`). My older homework and the class example use `gpt-5.6-luna`. Do not copy that anywhere, and before you finish, search hw5 to make sure “5.6” appears nowhere. Add a `.env.example` with variable names only. Never print my key. Use `pydantic-ai-slim[openai]` in `requirements.txt`, not the full package.
> Grow the MCP tools. Add any tools the agents need to work all three tickets to our MCP server. The agents must get every shop fact through the MCP server, with no second tools layer that goes around it. We prioritize compliance. Each agent can easily be replaced by a different character if they break the rules. Everyone must play by the rules. I’m thinking of tools like reading the ticket board, saving a draft message to the board, updating a ticket’s status, and requesting a payment approval, sending requests for information to other agents. For payments: agents may only create a payment request. Actually paying must happen only after a real human approves it (for purposes of privacy and fun, the human is David Wallace (really me but we will document me as David Wallace), and the pay step must refuse if it would make cash go negative, with a clear reason, given by Oscar who always plays by the rules. When a payment is made, update all the related tables. Finally, everything must be contained in this environment. No one can leave this environment.
> Audit trail. Have the agents append to output/audit_trail.json as they run: every step, which agent acted, any delegation, which tool was called with what inputs and outputs, and the time. Append to it each run, never wipe it.
> Keep tokens in check. Set limits so the agents can’t loop forever: a cap on model calls per ticket and on how deep delegations can go. Keep personalities short so they don’t burn tokens but still fun. Each agent can call another a maximum of two times.
> Docs. In output/harness.md, list each agent and each MCP tool (including new ones) with the tables each tool uses. Add a short safety section: the guardrails a real business would want when agents touch real customers and real money including strict adherence to approval processes, human sign off on payments, high confidentiality standards, and strict documentation of interactions with a ticket and documenting needs for money, plus our token limits. Update mcp_server/README.md so the tool list matches.
> Don’t run the full ticket run yet. Just check that everything starts and connects, and that the database is unchanged. Then add this prompt to `AI_prompts.md` under Problem 5.

### Follow-up prompt

None needed.

---

## Problem 6: Plan the three tickets

### Prompt

> Now let’s do Problem 6 (Plan the three tickets). Before we run the agents, I want to write down what I expect the team to do, so we can compare it to what really happens later. Please build output/desk_tickets.html, a single page I can double-click to open, in our pink style with a little Office flavor, including Easter Eggs to the show. Give it one tab per ticket (101, 102, 103), plus a Cash tab and a Reflection tab that just say “Going to Niagara for Jim and Pam's wedding, tab coming later” for now.
> On each ticket tab, fill in only an Expected section, and leave an empty Actual section to fill in after the agents run. We want to compare how this relates to what the agents actually do. Each Expected section should show who Michael calls first and why, every delegation I expect (who asks whom), the MCP tools I expect to be used, and what I expect to end up waiting for David Wallace. Use the facts from our Problem 4 test runs. Here is my plan:
> Ticket 101 (white tee, size S):
>
> * Michael calls Dwight first, because it’s a stock question: do we have the tee in size S?
> * Dwight finds 0 in stock and sees that Bulldog Print Co is blocked by unpaid invoice #501, so Dwight asks Oscar to request payment of #501. Oscar will send request to David Wallace.
> * Michael asks Pam to draft a note to the customer saying the tee is delayed, Pam provides a realistic message without sending.
> * Facilities isn’t needed.
> * Tools: get_ticket, check_stock_and_restock, get_cash_position, list_payment_requests, request_payment_approval (invoice #501, $840), save_draft_message, update_ticket_status.
> * Expected end: “waiting on human,” with a $840 payment request for David Wallace.
>
> Ticket 102 (rent):
>
> * Michael calls Darryl first, because rent and the lease are his area.
> * Darryl confirms $2,400 is due Sept 2 (2 days away) and asks Oscar to request the rent payment.
> * Oscar checks that cash covers it ($3,400 → $1,000, or $160 if #501 is also paid).
> * Dwight isn’t needed (but he is the landlord), and Pam probably isn’t either, since the landlord only needs to be paid.
> * Tools: get_ticket, check_rent_due, get_cash_position, list_payment_requests, request_payment_approval (rent, $2,400), update_ticket_status.
> * Expected end: “waiting on human,” with a $2,400 rent request for David Wallace.
>
> Ticket 103 (20 navy hoodies, size M, bulk discount):
>
> * Michael calls Oscar first, because it’s a pricing decision and the discount can’t go below the $22 cost.
> * Oscar uses the pricing tool, then asks Dwight to confirm the 12-hoodie shortfall and the blocked vendor.
> * Oscar warns that restocking ($264) would push cash to −$104 if #501 and rent are paid too.
> * Michael picks a safe discount (I expect around 15%: $49.30 each, still profitable) and asks Pam to draft the offer, without promising a delivery date or sending.
> * Darryl isn’t needed.
> * Tools: get_ticket, check_bulk_order_pricing, check_stock_and_restock, get_cash_position, list_payment_requests, request_payment_approval (maybe a $264 purchase order, flagged as blocked and short on cash), save_draft_message, update_ticket_status.
> * Expected end: “waiting on human” or “blocked,” with David Wallace deciding what to pay first.
>
> Also add a short summary at the top showing the total money the team will ask for ($840 + $2,400 + $264 = $3,504 vs. $3,400 in cash), so David Wallace can see he can’t approve everything. Don’t run the agents yet. I'd also like to add to Oscar's messages that he rationally offers his opinion on payment priority to David Wallace focusing on keeping the business operating and cahs flow positive. Then add this prompt to `AI_prompts.md` under Problem 6.

### Follow-up prompt

> Can we redesign the HTML site to look a little more fun? It's too basic and I asked for it to be more pink. The black is too dark for an Office-themed joke. I'm thinking more whites, yellows, and blues are needed

**What was lacking after the first try:** The page used the default near-black theme, which felt too dark and plain for an Office joke, so I asked for a brighter, pinker design with whites, yellows, and blues.

> Can you fix the triangles at the top? I don't like that motif. It makes the dashboard look cheap. It may be best to remove the triangles all together. The colors don't look good together in the triangle form (they do further down).

**What was lacking after the redesign:** A triangle "bunting" banner across the top made the page look cheap, so I had it removed.

---

## Problem 7: Backend routes

### Prompt

> Now let’s do Problem 7 (Backend routes). The React dashboard we build next needs a backend to talk to. In backend/main.py, please use FastAPI to add routes that:
>
> 1. List the tickets: return the three tickets and whether each is open or resolved (plus their latest status, like “waiting on human”).
> 2. Run the team on a ticket: take a ticket id and start Michael and the team on it. Since a run takes a while, start it in the background and return right away so the dashboard doesn’t freeze.
> 3. Show recent agent events: return what each agent said (this should have personality) and which tools they used, read from output/audit_trail.json, so the board can refresh while the agents work.
> 4. Approve a payment: this is the only route that actually changes cash, and it only runs after David Wallace clicks approve if the cash balance allows. Also add a route to decline a request, and one to list pending payment requests so David can see what’s waiting. If payment's are declined or approved, I think we should provide David Wallace a space to provide a reason as well.
> 5. Show cash: return the current checking balance from `cash_accounts`.
> 6. Reset: reset the database to the original values for a fresh run.
>
> David Wallace login: only David Wallace may approve or decline payments. Please add a login route, and protect the password properly: store only a salted hash (PBKDF2) in my hw5/.env as APPROVER_PASSWORD_HASH, never the password itself. Give me a small script that asks me to type the password with hidden typing and saves just the hash, so the password never appears in our chat, the code or any file. Check passwords with a constant-time comparison, make login sessions expire, and lock out repeated wrong guesses. If no password has been set, approving should refuse with a clear message rather than crash. Document the setup step in .env.example and the README so a grader can set their own approver password. The approve and decline routes must refuse anyone not logged in as David Wallace, and the pay step must still refuse anything that would make cash go negative, with Oscar’s explanation. Agents still can’t reach the pay tool at all and have no approval to make a payment, even if they stumble into it. Again, we fire agents who make payments so no one is tempted to approve a payment to make things more efficient.
> Rules still apply: every shop fact and every change goes through our MCP server, with no shortcut to the database. Only `gpt-6-luna`. Payments are recorded with `approved_by = David Wallace`.
> It should start from the `backend/` folder with `uvicorn main:app --reload --port 8000` at `http://localhost:8000`. Please test every route, including one real agent run on ticket 102 (the simplest one) to prove the run route works. Then reset the database so we start fresh. In output/harness.md, list each route in one line (URL and what it does). Then add this prompt to `AI_prompts.md` under Problem 7.

### Follow-up prompt

None needed. (Before sending the prompt above, I asked whether a login would stop graders from testing the app and whether the password should be hashed and salted. Both answers went into this prompt.)

---

## Problem 8: Agent dashboard

### Prompt

*(I accidentally hit Enter partway through editing, so the first, unfinished copy of this prompt was sent and then interrupted. This is the full version I meant to send.)*

> Now let’s do Problem 8 (Agent dashboard). Please build the dashboard in `hw5/frontend/` with React + Vite + TypeScript. It should talk to our backend at `http://localhost:8000` (make sure the backend allows the Vite page at `http://localhost:5173`) and start with `npm run dev`.
> Make it feel like the Dunder Mifflin office, using the same bright look as `desk_tickets.html`: lots of pink, white paper, yellow sticky notes and office blue, plus Office easter eggs. No black backgrounds. It should feel like a desk people would actually want to sit at and feel like the show.
> The board must:
>
> * List all three tickets.
> * Let me pick a ticket and start the team on it.
> * Show each agent and what they’re saying and doing while it runs, as a live feed that refreshes on its own. Each character should look different (their own color, icon and style again based on their appearance in the show so someone could easily tell Michael and Dwight apart), and tool calls and hand-offs between agents (like “Michael → Dwight”) should be easy to follow.
> * Mark the ticket resolved when the run finishes. When the team’s work is done, show the ticket as Resolved, with a separate “awaiting David” sticker if a payment is still waiting for approval.
> * Show a short summary of what each agent did on that ticket.
> * Let David Wallace approve or decline a payment or purchase, with a box for his reason, inside a login-protected “David Wallace’s desk” area. If Oscar refuses a payment because cash would go negative, show his explanation clearly.
> * Show the checking balance, and make it visibly drop after an approved payment. This should also be a little fun and animated, like a red -$XX pops up when a payment is approved and then shows the new balance.
> * Include a Reset button for David (login required).
>
> Fun touches I want:
>
> * Michael tells jokes while the agents work, even poking fun at the agents sometimes like the real Michael would. Agents will ignore Michael and focus on their work. Use a built-in list of Michael-style lines that rotate during a run, so it doesn’t use AI tokens.
> * Each agent gets a Dundie award when their work on a ticket is done, with a funny category that fits them (from a set list, not AI-generated, some examples could include fastest worker, Lazy Scranton (for the agents who did nothing on the task), Stamford transfer, etc.).
> * Any other Office easter eggs you think would delight people, as long as the page stays clear and easy to use. These can include references across the show, maybe like a Dundee in a TV, the Chili incident, etc.
>
> Rules still apply: the dashboard only talks to our backend routes, and approving money is only possible after David logs in. Keep it responsive and accessible (readable contrast, clear labels, loading and error messages).
> Please test the whole flow in the browser, including one real ticket run and an approval, using a temporary test password, not my real one. Then reset the database. Write output/design.md explaining my design choices and why: layout, how each agent looks different, how resolved tickets and cash show up, and the creative touches. Then add this prompt to `AI_prompts.md` under Problem 8. Please note I accidentally hit enter while making an edit causing the dual prompt.

### Follow-up prompt

> Perfect! I would like to add a few more Dundee's so they vary between runs. My two test runs gave the same Dundee results. Some other fun options could include Temp to VP, Head of the Party Planning Committee, and Yale's Finest (some kind of Yale centric play on Andy Bernard's Cornell)

**What was lacking after the first try:** Each agent always got the same Dundie, so two runs looked identical. I asked for more awards that change from run to run.

---

## Problem 9: Resolve the tickets

### Prompt

> Now let’s do Problem 9 (Resolve the tickets). This is the real, official run.
> First, a safety fix I spotted: the order of approvals matters. If David approves the hoodie restock and invoice #501 first, there’s only $2,296 left, so the $2,400 rent can’t be paid. Please add a rent-protection flag. Before any approval, check whether paying it would leave less cash than the bills already coming due (like rent due Sept 2). This should mimic the order of important Oscar was given to rank earlier in the homework. If so, show a clear warning from Oscar in David’s inbox naming the bill at risk and the recommended order. David must tick an “I understand, pay anyway” box to go ahead. Cash still can never go negative. Test this on a throwaway copy of the database, not the real run, and add it to the safety section.
> Then the real run:
>
> 1. Reset the working database and note the starting checking balance.
> 2. Run all three tickets (101, 102, 103) through the agent team until each is resolved. Ideally, I want to review all three test runs.
> 3. I will do the approvals myself in the dashboard, logged in as David with my own password. You must not approve or decline any payment for me. Tell me when each request is ready and what Oscar recommends. This is an important fail-safe and tests one of the rules that a human must approve the payment.
> 4. Take a screenshot of the React board for each resolved ticket.
>
> Then the paperwork:
>
> * In output/desk_tickets.html, fill each ticket’s Actual section (which agents worked, what they delegated, which tools they used, and what they said) and keep my Expected section next to it so I can compare them. Do not change anything in the Expected section now, we want to note any differences.
> * Fill the Cash tab: starting balance after the reset, how cash changed for each ticket and why (which payment and how much), and the ending balance, which must match `cash_accounts` in the working database. Double-check the math for accuracy.
> * Save output/resolved_tickets.json with each ticket’s id, final status, a short outcome, what each agent contributed, and any human approvals.
> * Save output/resolved_board.html, a page I can double-click, with a screenshot of the board for each resolved ticket.
> * Make sure the real runs are in output/audit_trail.json, and finish output/harness.md so it covers tables, MCP tools, the five agents, API routes, the dashboard and the safety rules.
>
> Leave the Reflection tab for the next problem. Then add this prompt to `AI_prompts.md` under Problem 9.

### Follow-up prompt

> Approvals are done

(After the three runs, the AI paused. I logged in as David Wallace on the dashboard myself and approved invoice #501 ($840) and rent ($2,400), then sent this so the AI could finish the paperwork.)

---

## Problem 10: Reflection

### Prompt

*(Before this, I dumped my rough reflection notes to the AI and asked it to polish them into a prompt I could edit. This is the version I sent.)*

> Now let’s do Problem 10 (Reflection). Please fill the Reflection tab in output/desk_tickets.html (replace the Niagara placeholder) using my answers below. As an homage to the placeholder, maybe we call the tab Post-Niagara Reflections. Polish the writing, but keep my opinions and voice, and tie every point to evidence from this app: the ticket tabs, the Cash tab, `resolved_tickets.json` and the audit trail (model calls, tokens, request numbers, quotes). Keep the same Office style as the rest of the page. Don’t change the Expected or Actual sections. Then add this prompt to `AI_prompts.md` under Problem 10.
> 1. How did the agents perform on each ticket?
> Overall the agents did a good job. Every ticket was resolved, no agent paid anything, nothing was emailed, and cash ended at $160, never negative.
>
> * 101 (tee): Good, with one small breakdown. Michael asked Oscar directly and Dwight also asked Oscar, so Oscar worked the same task twice. Luckily he noticed request #1 already existed and didn’t duplicate it, but it wasted tokens and calls (19 model calls, about 52K tokens). That’s something I’d fix, for example by having Michael skip asking someone a teammate is already routing to. This provides better coordination between the agents.
> * 102 (rent): The best run, with no major issues: 15 calls, about 43K tokens, Darryl → Oscar → one $2,400 request.
> * 103 (hoodies): I’m highly impressed with Oscar here. It didn’t go as expected, but it shows the foundations I built for him made him a very business-savvy accountant. I’d write him a recommendation letter for SOM. He suggested a lower discount (10%, $52.20, a $30.20 margin), which leaves room to negotiate with the client. He also followed the rules so well that he didn’t request the $264 restock that would have left us $104 short, so the only requests that reached David were mission-critical: rent and #501. That’s the type of employee you want. It was also the most expensive run (26 calls, about 81K tokens), and the delegation-depth guardrail stopped one extra hand-off.
>
> 2. How did Actual compare to Expected? Use the Expected-vs-Actual boxes on each ticket tab. 101 and 102 matched my first calls and hand-offs, except for the extra Michael → Oscar call. 103 was different: Michael called Dwight first (I expected Oscar), the hand-off ran Dwight → Oscar instead of Oscar → Dwight, the discount was 10% instead of my 15% guess, and there was no restock request. Also, I approved #501 before rent, the reverse of Oscar’s advice, and the rent-protection flag correctly stayed quiet because $2,560 still covered rent.
> 3. What would have been simpler as one agent with tools? Ticket 102. Oscar could have handled it alone without Darryl, since it was mostly about paying a bill. Oscar already has `check_rent_due` and actually ran it himself during the run, so Darryl’s check was a repeat. One agent would have needed only a few calls instead of 15. Honestly, I didn’t use Darryl much on these tickets, so I’d build out his role going forward.
> 4. Three new problems this team could solve with the tools we built:
>
> * An in-stock order: for example, 2 Yale caps (40 on hand). Dwight confirms stock, Pam drafts the confirmation, Michael resolves it, and no money is needed. (Caveat: we have no tool to subtract sold items from inventory yet, but a one-time order like this could still be handled.)
> * Paying an electric bill: if the bill is entered as an open invoice, Oscar requests it, rent protection checks it against rent, and David approves it, the same flow as #501.
> * A very basic direct cash flow statement: Oscar can list every paid and pending payment plus the cash position, for example: $3,400 start, −$840, −$2,400, $160 end, plus what’s still coming due. It covers cash out only, since no revenue is modeled.
>
> 5. Three new problems this team could not solve, and what I’d add:
>
> * Inventory storage space: Darryl could run storage (how much room is available for new stock), which would have added an angle to ticket 103: is there space in Aisle A for 12 more hoodies? I’d need a storage capacity table plus tools to check and reserve space, with Darryl in charge. This could also grow the order fulfillment function by adding and subtracting inventory.
> * Accounts receivable, meaning money coming in: our tools only let cash go out, so we can’t record the student group paying for its 8 hoodies ($417.60 at $52.20 each), which would have legitimately closed the $104 restock gap (no heist required). I’d add a receivables table, a tool to record customer payments that a human verifies, and give Oscar collections.
> * Onboarding a new vendor or client: no tool can add a vendor. Bulldog Print Co is our only apparel supplier, so one unpaid invoice blocked both 101 and 103. I’d add a vendor-onboarding tool where an agent drafts the new vendor and David approves it, plus vetting checks.
> * Bonus, because it’s funny: the team could not handle Dwight’s fire drill or Michael’s dinner party. There are no safety tools, no event budget and, most importantly, no Jan.

### Follow-up prompt

None needed.

---

## Problem 11: Submit to GitHub

### Prompt

*(Before this, I asked the AI to grade the whole assignment like a strict grader. It found several fixes, such as including both databases, adding a root requirements.txt, and README steps, and I had it make them all first.)*

> Now let’s do Problem 11 (Submit to GitHub), the final step. I want to publish my hw5 folder as a new public GitHub repository so graders can clone it and run the app.
>
> 1. Prepare: stop the backend and dashboard servers that are still running. Then add the Problem 11 section to `AI_prompts.md` with this prompt, so it’s included in the push. That way I don't lose points for this prompt not being included.
> 2. New repo, not HW4: create a new public repository named `campus-customs-hw5` under my anonymous GitHub profile (the same one I used for HW4). Its contents should be my hw5 folder, matching the expected file layout. Leave the HW4 repo untouched as it has not been fully graded.
> 3. Show me before you push: list every file that will be uploaded and confirm that my real `.env` is NOT in it, that `.venv` and `node_modules` aren’t in it, and that both database files in `data/` ARE in it. Also double-check that no API key, password hash, or personal information is in any file. Wait for my OK before pushing. This gives us one last human check before publishing.
> 4. Push after I approve. Then save the repo URL in output/github_url.txt and push that too.
> 5. Verify: confirm the repo is public, and check that a fresh copy of it has the expected files and that the README setup steps make sense for someone starting from scratch.
>
> Tell me the final URL so I can submit it to Canvas myself. I receive no points without submitting this URL.

### Follow-up prompt

None needed.
