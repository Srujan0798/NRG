/**
 * Simple static server + API proxy for E2E testing.
 * Serves the production build and proxies API requests to the backend.
 * Uses only Node.js built-in modules.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { pipeline } = require('stream');

const PORT = process.env.PORT || 3000;
const API_TARGET = process.env.API_TARGET || 'localhost:8000';

const STATIC_DIR = path.join(__dirname, '../dist/frontend');

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const API_PATHS = [
  '/login', '/refresh', '/logout', '/query', '/researchers',
  '/publications', '/stats', '/health', '/health/', '/consent',
  '/me', '/me/', '/audit', '/audit/',
];

function isApiPath(urlPath) {
  return API_PATHS.some(p => urlPath === p || urlPath.startsWith(p + '/'));
}

function serveStatic(req, res) {
  let filePath = path.join(STATIC_DIR, req.url === '/' ? 'index.html' : req.url);
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // SPA fallback
        const indexPath = path.join(STATIC_DIR, 'index.html');
        fs.readFile(indexPath, (err2, indexData) => {
          if (err2) {
            res.writeHead(404);
            res.end('Not found');
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(indexData);
          }
        });
      } else {
        res.writeHead(500);
        res.end('Server error');
      }
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
}

function proxyRequest(req, res) {
  const options = {
    hostname: API_TARGET.split(':')[0],
    port: API_TARGET.split(':')[1] || 8000,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: API_TARGET,
    },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    pipeline(proxyRes, res, () => {});
  });

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err.message);
    res.writeHead(502);
    res.end(JSON.stringify({ error: 'Bad Gateway' }));
  });

  pipeline(req, proxyReq, () => {});
}

const server = http.createServer((req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (isApiPath(req.url)) {
    proxyRequest(req, res);
  } else {
    serveStatic(req, res);
  }
});

server.listen(PORT, () => {
  console.log(`E2E test server running on http://localhost:${PORT}`);
  console.log(`Proxying API requests to ${API_TARGET}`);
});
