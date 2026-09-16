# Sales Funnel — Wiring Guide

The full system: **traffic → landing page → free audit (lead magnet) → 6-email nurture → booked call → deposit via Stripe**.

## What's in here

```
sales-funnel/
├── site/
│   ├── index.html        Landing page (leads capture wired, demo mode)
│   └── thank-you.html    Post-signup page (sets expectations, booking CTA)
├── emails/
│   └── sequence.md       6-email nurture sequence, fully written
└── README.md             This file
```

## The funnel logic

Selling a **service** (web app builds), the funnel is NOT checkout-first. It's:

1. **Landing page** converts cold traffic with the "agency quality, freelancer price, days not months" hook
2. **Free 10-point site audit** = the lead magnet (low friction, demonstrates competence, natural bridge to a call)
3. **Email sequence** builds trust and handles the three objections: price ("where'd the agency markup go?"), speed ("how so fast?"), and quality ("is it actually good?")
4. **15-min scoping call** = the conversion event
5. **50% deposit via Stripe** (optional, for leads who want to pay before the call)

The audit is delivered manually by you — that's intentional. It qualifies the lead AND is your best sales asset.

---

## Step 1 — Set your real details (10 min, before anything else)

In `site/index.html`:
- [ ] Replace portfolio placeholders (holiday home site, personal site) with **real screenshots + links** — this is your #1 conversion driver
- [ ] Set real prices in the pricing section (draft numbers are marked with ⚠)
- [ ] Swap "Kyle Monk" title/copy if you want different positioning

In `site/thank-you.html` + `index.html`:
- [ ] Set `BOOKING_URL` / `FORM_ENDPOINT` (next steps below)
- [ ] Replace `hello@yourdomain.com` with your real email

## Step 2 — Bookings (5 min)

1. Sign up at [cal.com](https://cal.com) (free) → create a 15-minute event called "Scoping Call"
2. Put the link in **two places**:
   - `thank-you.html`: `const BOOKING_URL = "https://cal.com/you/15min"`
   - `index.html`: the `data-booking` link in the final CTA section
   - Email 5 of the sequence (`BOOKING_LINK`)

## Step 3 — Email capture (10 min, free)

**Simplest (recommended to start): [Formspree](https://formspree.io)**
1. Create a form → copy your endpoint URL
2. In `index.html`, set: `const FORM_ENDPOINT = "https://formspree.io/f/xxxxxxx";`
3. Leads arrive in your inbox; you reply manually at first (fine under ~20 leads/week)

**Scale-up path:** point Formspree's webhook (or use [Netlify Forms](https://docs.netlify.com/forms/setup/) if you host there) at [MailerLite](https://mailerlite.com) / Brevo (both free tiers) → import the 6-email sequence from `emails/sequence.md` → automation runs itself.

## Step 4 — Deploy (5 min, free)

**[Netlify Drop](https://app.netlify.com/drop)** — drag the `site/` folder in. Done. Free HTTPS + custom domain support.
Then connect your domain (e.g. `kylemonk.dev` or your brand domain) in Netlify's domain settings.

## Step 5 — Stripe checkout for deposits (15 min, optional)

For leads ready to pay before/after the call:
1. [Stripe Dashboard](https://dashboard.stripe.com) → **Payment links** → create "50% project deposit" links at each price tier (£375 / £900 / £2,000)
2. Send the right link over email after a verbal yes — no website integration needed
3. When volume justifies it, embed payment links as buttons on the pricing cards

## Step 6 — Traffic (you're starting from zero — the plan)

With no audience, pick **two** channels max. Ranked for a solo web developer:

| Channel | Why | Cadence |
|---|---|---|
| **Local business outreach** | Highest ROI. Audit local businesses' sites yourself (they're mostly bad), email them 3 specific fixes, offer the free audit. Warm, targeted, zero cost. | 10/day, personalized |
| **Build-in-public on X/LinkedIn** | Post before/after rebuilds of ugly local sites. The visual contrast IS the ad. | 3–4 posts/week |
| **Reddit/communities** | r/smallbusiness, r/Entrepreneur, local FB groups — answer "who can build my site" threads helpfully | Daily, 10 min |
| **SEO (long game)** | The landing page + a few blog posts ("how much should a website cost UK") compound over months | 1 post/week |

**The core loop for a zero-audience freelancer:** find a business with a bad site → make one specific improvement suggestion publicly or personally → they visit the landing page → free audit → call → project. Every project ships → becomes a portfolio piece + social proof → next loop is easier.

## Testing the funnel locally

Open `site/index.html` in a browser — it runs in **demo mode** (leads saved to localStorage, no backend). Submit the form → redirected to thank-you page → inspect leads with browser DevTools → Application → Local Storage → `leads`.

## Metrics to watch

- Landing page → email signup rate (aim 3–5% cold, 10%+ warm)
- Signup → audit request (aim 30%+ — the sequence pushes this)
- Audit → call booked (aim 25%+ — depends on audit quality)
- Call → closed project (aim 30–50%)

If a stage underperforms, fix THAT stage, not the whole funnel.
