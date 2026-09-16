# Pipeline — Operating Manual

The board (`site/pipeline.html`) is the tool. This is how you run it.
Your only job: **keep leads moving right.** A lead without a next action is a dead lead.

## Stages & exit criteria

| Stage | Lead is here when… | To move it right, you must… | Never sits longer than |
|---|---|---|---|
| **1 Prospect** | Found them (bad site, local business, referral) | Send first-touch email/DM | 2 days |
| **2 Contacted** | First touch sent, no reply | Follow up ×3 (below), each adding value | 3 days between touches |
| **3 Audit** | They replied / requested audit | Deliver the 10-point audit within **48h** | 48 hours |
| **4 Call booked** | Audit delivered, call scheduled | Take the call → send fixed quote within **24h** | — |
| **5 Quoted** | Quote sent | Follow up at day 2, 5, 10. Then it's won or lost | 10 days → decide |
| **6 Won** | Deposit paid (Stripe link) | Kick off build sprint same day | — |
| **✕ Lost** | They said no / went quiet | Log WHY in notes (price? timing?), set a follow-up ~90 days out | revisit quarterly |

## Non-negotiable rules

1. **Every card has a due date.** Overdue red = today's to-do list. No exceptions.
2. **Respond to any reply within 1 hour** when possible — speed of response is the single strongest predictor of closing service work.
3. **3-touch follow-up for cold outreach**, then mark Lost:
   - Touch 1: value ("noticed X on your site — here's the fix")
   - Touch 2 (day 3): proof (a before/after, or the free audit offer)
   - Touch 3 (day 7): close-the-loop ("should I leave you alone?") — gets surprisingly high reply rates
4. **A quote older than 10 days gets a decision, not another nudge.** Ask directly: "Is this a 'no'? Totally fine — I'd rather know."
5. **Lost ≠ dead.** 90-day revive list: businesses get new budgets, owners change minds.

## Daily rhythm (60–90 min until pipeline is full)

| When | What | Target |
|---|---|---|
| Morning | Check board. Clear every overdue card (follow-up or stage move). | zero overdue |
| Morning | Prospecting: find 10 businesses with weak sites, add as Prospects | 10/day |
| Midday | Send 10 first-touch emails (2 specific observations each — not templates) | 10/day |
| Anytime | Reply to replies within the hour | <1h |
| Friday | Review: stage conversions this week (below), kill what's not working | 20 min |

At ~10% first-touch reply rate: 10/day → 5 conversations/week → ~2 audits → ~1 call → a project every 1–2 weeks. That's the math for a full calendar within a month.

## Numbers to check every Friday

The board tracks open value + won value. You track conversion (export CSV, or eyeball counts):

- **Prospect → Contacted:** are you actually sending the 10/day? (activity, not conversion)
- **Contacted → Audit:** below ~8% replies? Your first-touch email is too generic — add more specificity about THEIR site
- **Audit → Call:** below ~40%? The audit is too shallow — make it more specific, rank fixes by impact
- **Call → Quoted → Won:** below ~50% won from quote? You're quoting too high for the value shown, or too slowly
- **Open pipeline value ≥ 3× monthly revenue goal.** Below that, prospect more; nothing else fixes it.

## Where the pieces connect

```
Prospecting (10/day, manual)          ──► pipeline.html (Prospect)
First-touch email (manual, specific)  ──► stage 2 · due = +3 days
Landing page signup / audit request   ──► add to board as stage 3 · due = +48h
Audit delivered (email 1 of sequence also fires if via landing page)
Call booked (cal.com)                 ──► stage 4
Quote sent (email + Stripe deposit link on acceptance)
Deposit paid                          ──► stage 6 · Won
```

## First-touch email template (personalize the [brackets] — always)

> Subject: [Business name]'s site — one quick thing
>
> Hi [Name] — I build websites for local businesses and I was looking at [site] today.
>
> One thing: [specific observation — e.g. "the menu is unreadable on iPhone, and that's ~60% of your visitors" / "the site takes 7 seconds to load on 4G — Google's data says most visitors leave by 3"].
>
> I put together a free 10-point teardown for businesses like yours — what's slow, what's costing you bookings, what to fix first. Want me to run one on [site]? No charge, no catch, useful even if you never hire me.
>
> — Kyle
> [landing page URL]

## Housekeeping

- Data is in your browser's localStorage — **Export CSV every Friday** (button in the header). Import restores/merges on any machine.
- Pipeline review IS the Friday export: keep the CSVs, they're your conversion history.
