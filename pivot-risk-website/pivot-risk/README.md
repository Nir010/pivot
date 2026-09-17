# Pivot Risk Pvt. Ltd. — Website

A static, 5-page site (Home, About, Services, Team, Contact) for Pivot Risk
Pvt. Ltd., Kupandole, Lalitpur. Plain HTML/CSS/JS — no build step, no
framework, so it deploys to Vercel with zero configuration.

## Preview locally

You don't need Node for the site itself, only to run a local server so
relative paths behave the same as they will in production.

```bash
npx serve .
```

Then open the printed local URL (usually http://localhost:3000).

## Deploy to Vercel

**Option A — Vercel CLI**
```bash
npm i -g vercel
cd pivot-risk
vercel        # first deploy, follow the prompts
vercel --prod # promote to production
```

**Option B — Git + Vercel dashboard**
1. Push this folder to a GitHub/GitLab/Bitbucket repo.
2. In the Vercel dashboard, "Add New Project" → import the repo.
3. Framework preset: choose "Other" (it's a static site — no build command
   needed, no output directory override needed).
4. Deploy.

`vercel.json` already sets `cleanUrls: true`, so `/about.html` will also be
reachable at `/about` once deployed.

## What to edit before launch

- **Contact details** — email, phone, and address appear in the footer of
  every page and on `contact.html`. Search-and-replace
  `hello@pivotrisk.com.np` and `+977 1-000-0000` with the real ones.
- **Team page** (`team.html`) — all six profiles are placeholders (names,
  roles, bios, and initials-in-a-box photos). Replace with real people and
  swap each `<div class="photo">X</div>` for an `<img>` tag once you have
  headshots.
- **Services copy** (`services.html`, and the summary on `index.html`) —
  written from a generic risk-consulting brief. Adjust to match what Pivot
  Risk actually offers.
- **Stats row on the homepage** (`120+`, `35+`, etc.) — placeholder numbers,
  replace with real figures or remove the section.
- **Contact form** — currently client-side only (it shows a message instead
  of sending anywhere). To actually receive submissions, either:
  - point the form at a form backend like Formspree or Getform (swap the
    `<form>` tag's behaviour in `js/main.js`), or
  - add a Vercel Serverless Function (an `/api` folder) that emails you or
    writes to a database.
- **Map embed** on `contact.html` uses a keyless Google Maps embed query
  for "Kupandole, Lalitpur, Nepal" — fine for now, but for a pinned exact
  location, swap in an embed URL for your specific address.
- **Favicon** — none is set. Add a favicon file and link it from each
  page's `<head>`.

## File structure

```
pivot-risk/
├── index.html       Home
├── about.html        About
├── services.html      Services
├── team.html          Team
├── contact.html        Contact
├── css/styles.css      Design tokens + shared styles
├── js/main.js            Mobile nav, footer year, contact form handler
├── vercel.json
├── package.json
└── README.md          (this file)
```

## Design notes

Palette: ink navy (`#0f1b2d`), deep blue (`#1b3a5c`), a muted brass-gold
accent (`#b8923f`), and a cool paper background (`#f2f3f0`), with a rust
accent (`#9c4a30`) used sparingly for eyebrow labels. Headline type is
Fraunces (serif), body is IBM Plex Sans — loaded from Google Fonts in
`styles.css`. The thin contour-line motif in the homepage hero and the
faint risk-exposure chart are original SVG, not stock imagery.
