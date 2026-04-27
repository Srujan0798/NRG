# NRG Nginx Sovereign Skill

Nginx reverse proxy, SSL termination, security hardening, and Indian-soil hosting configuration for the National Research Graph (NRG).

## When to Use

Use this skill when:
- Configuring Nginx as the edge reverse proxy for NRG
- Setting up SSL/TLS with Indian-sovereign constraints
- Hardening Nginx against common attack vectors
- Debugging Nginx → Kong → upstream connectivity
- Implementing IP-based access controls for admin endpoints

## NRG Edge Architecture

```
Internet → Nginx (443/80) → Kong (8000) → NRG Services
              ↓
         SSL Termination
         Rate Limit (layer 4)
         WAF Rules
         GeoIP Blocking
```

Nginx is the single entry point. It handles TLS, static assets, and initial filtering before passing to Kong.

## Core Nginx Configuration

### `/etc/nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format with request timing
    log_format nrg_main '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_referer" "$http_user_agent" '
                        '$request_time $upstream_response_time '
                        '$http_x_forwarded_tier';

    access_log /var/log/nginx/access.log nrg_main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript;

    # Security headers (applied globally)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=1r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    include /etc/nginx/conf.d/*.conf;
}
```

### `/etc/nginx/conf.d/nrg.conf`

```nginx
# Upstream definitions
upstream kong_backend {
    server localhost:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream frontend {
    server localhost:5173 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name nrg.gov.in www.nrg.gov.in;
    return 301 https://$server_name$request_uri;
}

# Main API server
server {
    listen 443 ssl http2;
    server_name nrg.gov.in;

    # SSL Configuration (sovereign — Indian CA)
    ssl_certificate /etc/ssl/certs/nrg-gov-in.crt;
    ssl_certificate_key /etc/ssl/private/nrg-gov-in.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/nrg-gov-in-chain.crt;

    # Security
    server_tokens off;

    # API routes → Kong
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        limit_conn addr 10;

        proxy_pass http://kong_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Static frontend assets
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint (bypass auth)
    location /nginx-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

# Admin endpoint — IP restricted
server {
    listen 443 ssl http2;
    server_name admin.nrg.gov.in;

    ssl_certificate /etc/ssl/certs/nrg-admin.crt;
    ssl_certificate_key /etc/ssl/private/nrg-admin.key;
    ssl_protocols TLSv1.3;

    # Allow only internal VPC and specific IPs
    allow 10.0.0.0/8;
    allow 127.0.0.1;
    deny all;

    location / {
        proxy_pass http://kong_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Hardening Checklist

- [ ] `server_tokens off;` — hide Nginx version
- [ ] TLS 1.2+ only — no SSLv3, TLS 1.0/1.1
- [ ] Strong cipher suite — no weak ciphers
- [ ] OCSP stapling enabled
- [ ] HSTS header (after confirming HTTPS works)
- [ ] Rate limiting on all public endpoints
- [ ] Connection limiting per IP
- [ ] Admin endpoints IP-restricted
- [ ] No directory listing (`autoindex off;`)
- [ ] Request size limits (`client_max_body_size 10m;`)
- [ ] Timeouts configured (prevent slowloris)

### HSTS (enable after cert validation)

```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

## GeoIP Blocking (Optional)

Block non-Indian traffic if sovereign policy requires:

```nginx
# Requires nginx-module-geoip2 or GeoIP database
geoip_country /usr/share/GeoIP/GeoIP.dat;

server {
    if ($geoip_country_code != "IN") {
        return 403 "Access restricted to Indian territory\n";
    }
    # ... rest of config
}
```

**Note:** Only enable if explicitly required by policy. GeoIP databases require maintenance.

## Log Rotation

```bash
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nginx adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

## Debugging

```bash
# Test configuration
nginx -t

# Reload gracefully
nginx -s reload

# Check active connections
ss -tan | grep :443 | wc -l

# View real-time access log
tail -f /var/log/nginx/access.log | grep -v "nginx-health"

# Check SSL configuration
openssl s_client -connect nrg.gov.in:443 -servername nrg.gov.in < /dev/null

# Verify cipher strength
nmap --script ssl-enum-ciphers -p 443 nrg.gov.in
```

## Sovereign Constraints

1. **SSL certificates from Indian CA:** Use NIC, IDRBT, or government-approved CAs. No Let's Encrypt or foreign CAs for production.
2. **Keys never leave Indian soil:** Private keys stored on HSM or encrypted at rest on Indian servers only.
3. **No CDN:** No Cloudflare, AWS CloudFront, or foreign CDN. Static assets served from Indian edge nodes if needed.
4. **Logs stay local:** Access logs stored on Indian servers; no forwarding to foreign analytics services.
5. **Admin access VPN-only:** `admin.nrg.gov.in` accessible only via internal VPN or bastion host.

## SSL Certificate Paths

```
/etc/ssl/certs/nrg-gov-in.crt        # Server certificate
/etc/ssl/private/nrg-gov-in.key      # Private key (chmod 600)
/etc/ssl/certs/nrg-gov-in-chain.crt  # Intermediate chain
```

**Permissions:**
```bash
chmod 600 /etc/ssl/private/*.key
chown root:ssl-cert /etc/ssl/private/*.key
```
