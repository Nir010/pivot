# Pivot Risk Pvt. Ltd. — Website

A static, 5-page site (Home, About, Services, Team, Contact) for Pivot Risk
Pvt. Ltd., Kupandole, Lalitpur. Plain HTML/CSS/JS — no build step, no
framework, so it deploys to Vercel with zero configuration.

## Preview locally

Because the pages load the shared header/footer with JavaScript, they must be
opened over HTTP — opening the files directly from disk (`file://`) blocks that
and the header/footer won't appear. Use the included zero-dependency server,
which matches the deployed (Vercel) URLs:

```bash
npm start
```

Then open http://localhost:3000 — the home page loads directly, and
`/about`, `/services`, `/team`, `/contact` (and `/about.html` etc.) all work.
To stop the server, press Ctrl+C.

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
3. Set the Vercel **Root Directory** to `pivot-risk-website/pivot-risk`.
4. Framework preset: choose "Other". Leave the build command empty and the
   output directory empty.
5. Deploy.

The Vercel configuration must stay at `pivot-risk/vercel.json` (not inside
`html/`) so Vercel can serve the sibling `css/`, `js/`, and `images/`
directories. It rewrites `/`, `/about`, `/services`, `/team`, and `/contact`
to the matching files in `html/`.

## What to edit before launch

- **Contact details** — email, phone, and address appear in the footer of
  every page and on `contact.html`. Search-and-replace
  `hello@pivotrisk.com.np` and `+977 1-000-0000` with the real ones.
- **Team page** (`team.html`) — the two directors have real headshots
  (`udaya.png`, `krishna.png`); the seven member profiles still use placeholder
  stock photos (`boy.png` / `girl.png`). Replace those with real headshots as
  they become available.
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
├── html/                 All pages
│   ├── index.html          Home
│   ├── about.html          About
│   ├── services.html       Services
│   ├── team.html           Team
│   ├── contact.html        Contact
│   ├── header.html         Shared nav — loaded via js/main.js
│   └── footer.html         Shared footer — loaded via js/main.js
├── images/                logo.png, udaya.png, krishna.png, boy.png, girl.png
├── css/styles.css          Design tokens + shared styles
├── js/main.js              Loads header/footer, mobile nav, active link,
│                           footer year, contact form handler
├── server.mjs              Zero-dependency local server (npm start)
├── vercel.json             cleanUrls + rewrites for the html/ pages
├── package.json
└── README.md              (this file)
```

## Design notes

Palette: ink navy (`#0f1b2d`), deep blue (`#1b3a5c`), a muted brass-gold
accent (`#b8923f`), and a cool paper background (`#f2f3f0`), with a rust
accent (`#9c4a30`) used sparingly for eyebrow labels. Headline type is
Fraunces (serif), body is IBM Plex Sans — loaded from Google Fonts in
`styles.css`. The thin contour-line motif in the homepage hero and the
faint risk-exposure chart are original SVG, not stock imagery.
