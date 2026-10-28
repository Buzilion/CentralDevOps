# 04 — HTTP routing, forwarded headers, limits, and timeouts

## Learning objectives

You can route requests by hostname and path, forward only well-understood metadata, set bounded request and connection behavior, and avoid proxy changes that silently alter application semantics.

## Routing must match the application contract

The proxy can route on hostname and URL path, but path rewriting changes what the application receives. If the app expects `/api/orders`, forwarding that exact path differs from stripping `/api` and sending `/orders`. A trailing slash in an Nginx `proxy_pass` URI can change prefix-replacement behavior. Define the intended upstream request for representative paths before writing rules.

Prefer one explicit hostname/site per application. If serving multiple applications, route by a controlled `Host` name or clear path prefix and test collisions. Decide how unknown hosts and unknown paths behave. Avoid a catch-all that forwards every request to the main app unless that is the intentional default.

## Forwarding scheme, host, and client address

Applications commonly need the original host and scheme to build absolute links, secure cookies, redirects, and OAuth callback URLs. The proxy should preserve the intended host and set the external scheme. If TLS ends at the proxy but HTTP is used to the upstream, the app must know the public scheme is HTTPS through a trusted proxy mechanism; otherwise it may create HTTP redirects that loop or set insecure cookies.

Forwarded metadata is trustworthy only across a controlled boundary. For a direct Nginx edge, set the client address from `$remote_addr` rather than blindly appending incoming `X-Forwarded-For`. If a trusted CDN/load balancer sits in front, allow-list its published source ranges and configure the proxy to interpret their client-address header before forwarding it. Configure the application framework's trusted-proxy setting narrowly; never trust every network peer merely to make HTTPS detection work.

## Bound work deliberately

Request-body limits protect disk and memory, but must accommodate actual application operations such as uploads. Nginx's `client_max_body_size` can reject larger bodies before they reach the app; choose a justified limit and test the boundary. Apply limits where needed rather than setting an unnecessarily large global value.

Timeouts are limits on waiting, not a way to make a slow application reliable. Understand the difference between client send/read behavior and upstream connect/send/read timeouts. A timeout that is too short breaks legitimate long requests; an excessively long timeout lets slow clients or hung upstream work occupy resources. Prefer asynchronous job patterns for long-running work rather than retaining a web request indefinitely.

The proxy and application may each have body, header, and timeout limits. A request succeeds only if the whole path is compatible. Document the effective end-to-end limits and test normal and boundary cases.

## Security headers are application policy

The proxy can set headers such as `X-Content-Type-Options: nosniff`, a carefully chosen `Referrer-Policy`, and a frame policy. But a Content Security Policy must reflect the actual scripts, styles, APIs, fonts, and embedded content the application uses. A mistaken policy can break the app; a permissive policy may add no meaningful protection. Prefer application-owned policies where appropriate and test with browser developer tools.

Enable HSTS only after HTTPS is verified and all intended subdomains are ready for HTTPS. `includeSubDomains` and preload have broad consequences and are not routine defaults. Do not send conflicting copies of security headers from both app and proxy without understanding which value browsers will apply.

## Nginx WebSocket routing illustration

WebSockets begin as an HTTP request and then upgrade the connection. In Nginx, upgrade variables are typically defined once in the `http` context, then used by the relevant location:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

location /realtime/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 75s;
}
```

Use the actual WebSocket path and a timeout compatible with expected idle periods and keepalives. Do not raise the timeout for every route just because one real-time route needs it. Caddy's reverse proxy handles WebSocket upgrades automatically in ordinary configurations; still verify application authentication, origin checks, and idle behavior.

## Knowledge check

1. How can a trailing slash on `proxy_pass` alter a path-prefix route?
2. Why is a caller-supplied `X-Forwarded-For` not authoritative?
3. Which limits could reject an upload even if the proxy accepts it?
4. Why should HSTS subdomain/preload options not be enabled casually?

## Practical checkpoint

Record the upstream request path, body limit, timeouts, forwarded headers, and security-header ownership for the application. Implement only requirements found in the runtime contract in [Task 05 — Configure application routes, headers, and bounded request behavior](../tasks/05-configure-application-routes-headers-and-bounded-request-behavior.md).

## References

- [NGINX: ngx_http_proxy_module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [NGINX: WebSocket proxying](https://nginx.org/en/docs/http/websocket.html)
- [MDN: Strict-Transport-Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)
- [MDN: Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)
