---
name: create-contract
description: Set up a Bluejay customer's billing contract in Metronome the same way the internal dashboard's contract wizard does — look up the customer, pick or create a marked-up rate card, check the deal for billing traps, show a plain-English preview, and only after a yes, create the contract and verify it. Handles start-now contracts, replacing or adding to an existing contract, backdated starts, annual/quarterly/monthly terms, phone numbers, overages, Stripe invoice vs auto-charge, and YC/startup free months. Use when someone says "create a contract", "set up billing for <customer>", "move <customer> to a new rate card", "backfill a contract", "make a rate card", or pastes an order form.
---

# Create a Bluejay contract

Written for anyone on the team, technical or not. Talk in plain English. Never show raw JSON unless asked.

The one requirement: a **Metronome API key** in `METRONOME_API_KEY`. If it is missing, ask the user to
set it (Metronome → Settings → API tokens) and stop. A sandbox key works too and is the safe way to practise.

All Metronome calls go through `scripts/metronome_contract.py` (Python 3, standard library). It mirrors the
dashboard's code (`bluejay-ai-dashboard/lib/metronome/*`), so a contract made here is identical to one made
in the wizard. **Every write is a dry run unless `--apply` is passed.** Never pass `--apply` before step 6.

```
S=<this skill dir>/scripts/metronome_contract.py
python3 $S customer "<name or org id>"     # step 1
python3 $S rate-cards [--query tekion]     # step 3
python3 $S create-rate-card ...            # step 3, if a new card is needed
python3 $S create-contract ...             # step 5 dry run, step 6 --apply
python3 $S verify --customer-id .. --contract-id ..   # step 7
```

## The flow — always in this order

### 1. Find the customer
Run `customer`. Read back, in plain words: the Metronome customer id, the org id (`external_id`), whether
Stripe is linked and how (`send_invoice` / `charge_automatically`), every contract with its dates and term,
and credit balances. Note any active contract — step 5 needs to know whether to replace it or add beside it.

### 2. Get the deal terms
From the user, an order form, or a Slack thread they point you to. You need all of these — ask for any
that are missing, one short question at a time:

| Term | Notes |
|---|---|
| Fee per term | `--fee`. **$0 if the customer was already invoiced outside Metronome** (e.g. a founder sent the invoice by hand) — otherwise they get billed twice. Always ask. |
| Term | MONTHLY, QUARTERLY or ANNUAL. Match how they are **billed**, not how the price was quoted ("$3k/month, invoiced yearly" = ANNUAL with a $36k fee). |
| Credits per term | `--credits`. 1 credit = $1 of usage at the card's commit rate. Annual term = the whole year's credits up front. |
| Phone numbers | Quantity and price **per term** (`$3/month` = `$9` quarterly = `$36` annual). Numbers included in the deal → quantity 0, keep the price so extra numbers bill correctly. Quantity > 0 bills immediately at the start. |
| Overages | Allowed or not. |
| Start date | Always ask. Backdating is common. Keep the customer's existing billing anchor (same day-of-month and time) when you can — see step 4. |
| Billing | See "Invoice or charge?" below. |
| Start mode | Start now (this skill) or add to the customer's account as an offer (dashboard only — see "Not supported"). |
| YC / startup deal | `--free-months N`: $0 fee for N months, then the normal fee. **MONTHLY term only.** |

**Invoice or charge?** If the customer has a card or bank on file in Stripe → `charge_automatically`
(our default: "if we can charge, charge"). No payment method → `send_invoice` (auto-charge would fail on the
first invoice). This skill can't see Stripe — ask the user, or have them check the customer in Stripe. If they
want invoices but pay by wire, use `send_invoice`; when the wire lands, staff click **Mark paid** on the
dashboard's Pricing → Unpaid page (no Stripe fee on invoices paid outside Stripe).

### 3. Rates (k and m)
A rate card is our cost × **k** for usage inside credits and × **m** for overage. Run `rate-cards` to see
existing cards and their k/m. Reuse the customer's card if it exists.

To choose k for a new card, use the internal dashboard (anyone with dashboard access can read it):
- **Pricing → Price Calculator** — our cost per voice-simulation minute (platform-wide).
- **Pricing → Usage Costs**, filtered to the customer — what their actual usage costs us per month.

`price = our cost × k`. Explain the result per voice minute and, for text-heavy customers, per chat turn.
One k applies to everything — text is far cheaper for us than voice, so a single k cannot hit a high
per-chat-turn price and a normal per-minute price at once. Say so if the deal assumes it.
Overage: if the contract says overage credits "deplete ~20% faster", **m = 1.2 × k**.

Create a card with `create-rate-card --name "Bluejay - <Customer>" --k .. --m ..` plus
`--subscription-price TERM=DOLLARS` and `--phone-price TERM=DOLLARS` for each term you may use. These are
list prices; the contract sets the real fee and phone price per customer anyway. Dry run first, then `--apply`.

### 4. Check for traps
Say each one that applies, in one line:
- **Already invoiced elsewhere** → fee must be $0.
- **Credits period ≠ billing period** (e.g. yearly pool, monthly invoices) → the dashboard can't express it;
  term follows the billing. Raise it.
- **Overage billed monthly in the contract but the term is annual** → overage bills once a year. Raise it.
- **Phone price per term** — $3/month on an annual term is $36, not $3.
- **Phone numbers bill immediately** — every later number purchase creates its own small invoice.
- **Backdated start** — usage already recorded on the old contract moves to the new one; verify it in step 7.
- **Anchor** — `customer` shows the current billing anchor. Prefer a start on the same day-of-month and time,
  after the signing date, so the old contract ends exactly at its period boundary.
- **Active contract** — replace it (`--replace <id>`, ends it at the new start), take over its exact start
  (`--replace-at-its-start <id>`, archives it — only when the new deal should cover the old period too),
  or add beside it (`--add`).

### 5. Preview and confirm
Run `create-contract` **without** `--apply`. Turn its output into a short plain-English summary:

> Tekion moves from the free tracker to an **annual** contract on "Bluejay - Tekion" starting **Sep 5, 2026
> 11:00 AM PT**. Fee **$0** this year (already invoiced). **36,000 credits** for the year. 30 phone numbers
> included; extras $36/yr. Overage allowed. Invoices are **emailed** (send_invoice) to the Stripe customer.
> The free tracker ends at the same moment.

Also say what will be invoiced right away (phone numbers × price, a fee billed in advance, or a $0 invoice).
Then ask: **"Create it?"** Do nothing until the user clearly says yes.

### 6. Create
Re-run the exact same command with `--apply`. It ends/archives the old contract, links Stripe (if asked),
then creates the contract — the dashboard's order.

### 7. Verify and record
Run `verify`. Report: dates and anchor, fee and phone overrides, credits balance (for a backdated start the
balance should already be below the grant — usage moved over), and any invoices with their Stripe status.
Then tell the user the two things only the dashboard/database can do (below), and offer a Linear comment
with the contract id if the work has a ticket.

## Not supported here — stop and hand off
Never improvise Metronome calls outside the script. If a deal needs something below, say so plainly and
suggest a Linear ticket for engineering with the deal terms and what is missing.
- **"Add to customer's account" (offer)** — it saves a plan in our database. Use the dashboard wizard.
- **Org record update** — the dashboard also writes `stripe_customer_id` and `metronome_starts_at` on the
  org. Without it, automatic receipts for card customers (ENG-553) won't find the org. Ask an engineer, or
  create the contract from the dashboard when that matters.
- **Separate text vs voice pricing**, monthly overage on an annual contract, credits on a different cycle
  than billing, per-number phone billing on the next invoice instead of immediately.
- **Creating a brand-new Metronome customer** — signup normally creates one; if `customer` finds nothing,
  hand off.
