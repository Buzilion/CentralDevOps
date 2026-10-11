# 06 — Serving static assets, APIs, and WebSockets

## Learning objectives

You can distinguish an application-rendered route from a static asset or API route, preserve correct cache and error behavior, and verify WebSocket support only when the application requires it.

## First determine who serves each path

An app may serve HTML, JavaScript/CSS assets, API endpoints, uploaded files, and real-time connections itself. Another architecture builds a static frontend into files served directly by Nginx/Caddy while an API runs separately. Do not infer which applies from framework popularity: inspect the actual build output, Docker image, runtime configuration, and documented start command.

For each public path family, record:

| Path family | Handler | Upstream path transformation | Expected failure behavior |
|---|---|---|---|
| `/` and page routes | App or static server | Preserve or SPA fallback, explicitly chosen | App 404 or intentional client route |
| `/api/` | API app | Usually preserve API prefix unless app contract says otherwise | API status/body, never a silent HTML fallback |
| `/assets/` | App or static files | Preserve asset names | 404 for missing asset |
| `/uploads/` | App/storage service | Auth and range behavior as required | Avoid public access unless intended |
| WebSocket path | Realtime app handler | Preserve upgrade path | Bounded, observable handshake failure |

Paths here are examples only. The application's real API, static directory, and real-time paths must come from its source/configuration or verified runtime behavior.

## Static files and cache behavior

Static assets with content-hashed filenames can usually be cached for a long time with `Cache-Control: public, max-age=..., immutable`, because a content change creates a new URL. HTML entry points and other mutable manifests should not receive the same immutable lifetime; clients need to discover new asset names after a deployment. A stale HTML page referencing removed assets is a common bad-release symptom.

If a single-page application (SPA) uses client-side routes, it may need a fallback to its `index.html` for page navigations. Apply that fallback only to the intended frontend route space. An API 404 must not become `200 text/html` containing the SPA shell; this hides API errors and breaks clients. Ensure missing static assets remain real 404 responses rather than silently returning HTML.

When a proxy serves static files, it must be able to read the intended build directory with minimal privileges. Avoid writable application directories owned by the proxy unless the runtime specifically requires them. For uploads, prefer the application's designed storage path/service and authorization logic rather than an ad hoc public directory alias.

## API behavior and request size

APIs may use different payload sizes, methods, authentication, and timeout needs than page requests. If routes need distinct limits, isolate them with clear locations/handlers. Confirm that `OPTIONS` preflight/CORS behavior is owned by the app or deliberately configured at the proxy; do not add broad wildcard CORS as a generic fix. Preserve status codes and content types, and verify oversized requests fail intentionally rather than exhausting the host.

An upstream timeout should produce a diagnosable failure, not a fabricated success response. Avoid retrying non-idempotent requests at the proxy unless duplicate processing semantics are explicitly safe. The proxy should not cache authenticated or user-specific API responses by default.

## WebSocket behavior

WebSockets are optional. Enable support only if the application contract uses it. Verify the exact path, HTTP upgrade response, authentication and origin checks, heartbeat/keepalive behavior, and what happens when the upstream restarts. Long-lived connections consume resources, so size limits and timeouts should reflect expected use and be bounded. Ensure deployment/shutdown behavior can close or drain connections acceptably.

## Release implications

Proxy/static configuration and application images change on different lifecycles. If static files are deployed independently, coordinate asset compatibility with application releases. If the proxy serves assets embedded in the app image, deploy and roll back that image as one unit. In either case, test a browser's cache after release and rollback; configuration that works for one fresh browser may fail for users holding cached HTML or assets.

## Knowledge check

1. Why must API routes be excluded from a generic SPA `index.html` fallback?
2. What makes fingerprinted assets different from HTML for cache policy?
3. Why should proxy retries for POST requests be treated carefully?
4. Which WebSocket behavior should be tested beyond simply observing a 101 response?

## Practical checkpoint

Use the actual application to test its page routes, API errors, missing assets, upload boundary (if applicable), and real-time path (if applicable) in [Task 05 — Configure application routes, headers, and bounded request behavior](../tasks/05-configure-application-routes-headers-and-bounded-request-behavior.md).

## References

- [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [NGINX: ngx_http_proxy_module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [NGINX: WebSocket proxying](https://nginx.org/en/docs/http/websocket.html)
- [Caddy: File server](https://caddyserver.com/docs/caddyfile/directives/file_server)
