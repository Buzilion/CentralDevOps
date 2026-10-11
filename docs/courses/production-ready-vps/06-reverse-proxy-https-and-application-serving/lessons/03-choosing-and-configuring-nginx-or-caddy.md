# 03 — Choosing and configuring Nginx or Caddy

## Learning objectives

You can select one reverse proxy for a small VPS based on operational needs, understand its configuration lifecycle, and validate a minimal upstream route without confusing a successful proxy response with a secure production deployment.

## Choose an operator-owned design

Nginx and Caddy can both serve as a reverse proxy and TLS endpoint. Nginx is widely deployed, offers explicit configuration and a large operational ecosystem, and commonly uses a separate ACME client for certificate lifecycle. Caddy emphasizes simple configuration and automatic HTTPS, including obtaining and renewing certificates when its prerequisites are met. Both still require correct DNS, firewall, upstream, and application configuration.

Choose one proxy for the initial deployment. Running both for the same public address/ports creates an unnecessary listener conflict. Decide where it runs:

| Placement | Upstream path | Main operational concern |
|---|---|---|
| Host service | Loopback-published app port or host service | Package/service configuration, file ownership, host firewall |
| Container | Shared private Docker network to app service name | Publish only proxy ports; volume, certificate-data, and container lifecycle |

Do not mix host and container assumptions. `127.0.0.1` inside a proxy container refers to that container, not the VPS host or another container. Likewise, the Compose service name is normally resolvable only to containers on the same Docker network.

## Minimal Nginx shape

This fragment illustrates the concepts for an Nginx installation whose certificate paths are managed separately. It is not a drop-in full configuration. Use the installed Nginx version's supported syntax, verify includes and default sites, and replace every placeholder after the runtime contract is known.

```nginx
server {
    listen 80;
    server_name app.example.com;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name app.example.com;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/private-key.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

For a direct single-edge proxy, using `$remote_addr` avoids preserving a caller-supplied `X-Forwarded-For`. If another trusted load balancer precedes Nginx, configure its exact source ranges and real-IP processing before choosing what to forward. Add API-specific body limits, timeouts, WebSocket upgrade handling, and headers only when the application contract requires them. Do not copy snippets without checking their context; for example, an Nginx `map` belongs in the `http` context, not inside a `server` block.

## Minimal Caddy shape

For a hostname that resolves to this VPS and where the required inbound validation/HTTPS traffic can reach Caddy:

```caddyfile
app.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

Caddy can automatically obtain and renew certificates for a qualifying public hostname. Its data directory contains operationally important certificate/account state; protect and persist it according to the chosen installation method. Do not assume automatic HTTPS is possible for a private/unresolvable name or a blocked validation path. Review Caddy's trusted-proxy settings if another proxy/CDN is in front.

## Validate before applying

Configuration files are executable policy: a typo can prevent a reload, route requests to the wrong upstream, or expose an unintended listener. Keep changes in version control or an access-controlled configuration-management source. Back up the current file with permissions preserved, edit one logical change at a time, and run the proxy's native configuration check before reload.

Typical validation commands include `sudo nginx -t` for Nginx and `caddy validate --config /path/to/Caddyfile` for Caddy; exact commands and service names vary by installation. Prefer a reload when supported and validated. Observe the service state and logs immediately afterward. A successful syntax check proves configuration parseability, not correct routing, certificate validity, or public reachability.

## Default host and isolation

Handle unknown hostnames explicitly. Do not let arbitrary `Host` values select an unintended app. Keep the application upstream private, and test the upstream path from the proxy's actual network namespace. A `502 Bad Gateway` commonly means the proxy could not make a valid upstream connection; investigate that boundary rather than opening the upstream port publicly.

## Knowledge check

1. What is the difference between `127.0.0.1` inside a host proxy and inside a proxy container?
2. Which system manages TLS issuance and renewal in the chosen design?
3. What does an Nginx syntax check fail to prove?
4. Why should the default host not forward arbitrary names to the application?

## Practical checkpoint

Complete [Task 03 — Configure a minimal reverse proxy and prove private upstream access](../tasks/03-configure-a-minimal-reverse-proxy-and-prove-private-upstream-access.md). Add only the proxy family you have chosen; do not configure both.

## References

- [NGINX: Beginner's Guide](https://nginx.org/en/docs/beginners_guide.html)
- [NGINX: Reverse proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Caddy: Automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Caddy: Caddyfile](https://caddyserver.com/docs/caddyfile)
