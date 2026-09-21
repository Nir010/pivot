// Pivot Risk — minimal local server.
// Serves pages from html/ at clean URLs, mirroring vercel.json rewrites:
//   http://localhost:3000/           -> html/index.html
//   http://localhost:3000/about      -> html/about.html   (also /about.html)
//   http://localhost:3000/services|team|contact
// Run: npm start   (or: node server.mjs)

import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, extname, join, normalize, sep } from 'node:path';

const ROOT = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 3000;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

// mirrors vercel.json rewrites
const ROUTES = {
  '/': '/html/index.html',
  '/index': '/html/index.html',
  '/index.html': '/html/index.html',
  '/about': '/html/about.html',
  '/about.html': '/html/about.html',
  '/services': '/html/services.html',
  '/services.html': '/html/services.html',
  '/team': '/html/team.html',
  '/team.html': '/html/team.html',
  '/contact': '/html/contact.html',
  '/contact.html': '/html/contact.html',
};

const server = http.createServer(async (req, res) => {
  try {
    let urlPath = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (ROUTES[urlPath]) urlPath = ROUTES[urlPath];
    if (urlPath.endsWith('/')) urlPath += 'index.html';

    const filePath = normalize(join(ROOT, urlPath));
    if (filePath !== ROOT && !filePath.startsWith(ROOT + sep)) {
      res.writeHead(403, { 'content-type': 'text/plain; charset=utf-8' });
      return res.end('403 Forbidden');
    }

    let data;
    try {
      data = await readFile(filePath);
    } catch {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
      return res.end('404 Not Found');
    }

    res.writeHead(200, { 'content-type': MIME[extname(filePath)] || 'application/octet-stream' });
    res.end(data);
  } catch {
    res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('500 Internal Server Error');
  }
});

server.listen(PORT, () => {
  console.log(`Pivot Risk site running at http://localhost:${PORT}`);
});