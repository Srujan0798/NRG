/**
 * Simple static server + API proxy for E2E testing.
 * Serves the production build and proxies API requests to the backend.
 * Uses only Node.js built-in modules.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { pipeline } = require('stream');
const zlib = require('zlib');

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
  '.woff2': 'font/woff2',
};

const COMPRESSIBLE_TYPES = new Set([
  '.html',
  '.js',
  '.css',
  '.json',
  '.svg',
]);

function writeLog(message) {
  process.stdout.write(`${message}\n`);
}

function writeDiagnostic(message) {
  process.stderr.write(`${message}\n`);
}

const API_PATHS = [
  '/login', '/refresh', '/logout', '/auth', '/auth/', '/query', '/researchers',
  '/publications', '/stats', '/health', '/health/', '/consent',
  '/me', '/me/', '/audit', '/audit/', '/api/query/stream', '/api/telemetry',
];

function isApiPath(urlPath, method) {
  const pathname = new URL(urlPath, 'http://localhost').pathname;
  if (pathname === '/login' && method === 'GET') {
    return false;
  }
  return API_PATHS.some(p => pathname === p || pathname.startsWith(p + '/'));
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
    const acceptsGzip = /\bgzip\b/.test(req.headers['accept-encoding'] || '');
    if (acceptsGzip && COMPRESSIBLE_TYPES.has(ext)) {
      zlib.gzip(data, (gzipErr, compressed) => {
        if (gzipErr) {
          res.writeHead(200, { 'Content-Type': contentType });
          res.end(data);
          return;
        }
        res.writeHead(200, {
          'Content-Type': contentType,
          'Content-Encoding': 'gzip',
          'Vary': 'Accept-Encoding',
          'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=31536000, immutable',
        });
        res.end(compressed);
      });
      return;
    }
    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=31536000, immutable',
    });
    res.end(data);
  });
}

function proxyRequest(req, res) {
  let clientClosed = false;
  res.on('close', () => {
    clientClosed = true;
  });

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
    if (clientClosed || res.destroyed) {
      proxyRes.resume();
      return;
    }

    // Merge CORS headers into proxy response so browser can read the response
    const headers = {
      ...proxyRes.headers,
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };
    res.writeHead(proxyRes.statusCode, headers);
    try {
      pipeline(proxyRes, res, (err) => {
        if (err && !clientClosed && !res.destroyed) {
          writeDiagnostic(`Proxy response stream error: ${err.message}`);
        }
      });
    } catch (err) {
      if (!clientClosed && !res.destroyed) {
        writeDiagnostic(`Proxy response stream error: ${err.message}`);
        res.destroy(err);
      }
    }
  });

  proxyReq.on('error', (err) => {
    writeDiagnostic(`Proxy error: ${err.message}`);
    if (!clientClosed && !res.destroyed) {
      res.writeHead(502);
      res.end(JSON.stringify({ error: 'Bad Gateway' }));
    }
  });

  pipeline(req, proxyReq, (err) => {
    if (err && !clientClosed) {
      proxyReq.destroy(err);
    }
  });
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

  if (isApiPath(req.url, req.method)) {
    proxyRequest(req, res);
  } else {
    serveStatic(req, res);
  }
});

server.listen(PORT, () => {
  writeLog(`E2E test server running on http://localhost:${PORT}`);
  writeLog(`Proxying API requests to ${API_TARGET}`);
});
