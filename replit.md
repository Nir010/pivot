# Pivot Risk website

## Run

This is a static HTML/CSS/JavaScript website with a small Node.js server and
no dependency installation step. From the repository root, run:

```bash
npm start
```

The server uses `PORT` when provided and defaults to port 3000. The Replit
workflow runs it on port 5000 for the web preview.

## Project layout

- `html/` contains the five pages and the shared header/footer fragments.
- `css/`, `js/`, and `images/` contain the shared site assets.
- `vercel.json` is at the repository root for Vercel deployment.

The Vercel project root must remain the repository root. No nested root
directory setting is required.