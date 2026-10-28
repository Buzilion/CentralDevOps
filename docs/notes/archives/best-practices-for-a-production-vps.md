## 2. Other related concepts you should know

These tools overlap, but they solve different problems.

### A. Load balancer

Distributes traffic across multiple application instances.

Example: Nginx receives requests and distributes them across three Next.js instances. A load balancer may also perform health checks and stop routing to unhealthy instances.

When to use: When you need multiple instances for capacity or availability.

### B. Web Application Firewall (WAF)

Inspects HTTP requests and blocks traffic matching configured security rules, such as certain injection attempts or malicious request patterns.

Example: Cloudflare WAF protects your public website before traffic reaches your VPS.

When to use: When your public application needs an additional layer of HTTP attack protection. It does not replace application-level security.

### C. CDN (Content Delivery Network)

Caches and serves eligible content from locations closer to users, reducing latency and origin traffic.

Example: Cloudflare serves cached images and static assets while dynamic requests still reach your VPS.

When to use: When you need better global performance, caching, or edge protection.

### D. API gateway

Applies centralized policies to API traffic, such as API keys, quotas, consumer-specific rate limits, and routing rules. Kong, for example, implements API gateway functionality on top of reverse-proxy capabilities.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developer.konghq.com\&sz=32)

Kong Docs

+1



When to use: When you operate multiple APIs or need centralized API-consumer management.

### E. VPN or private network

Provides a private path for administrators or services to communicate without exposing every service publicly.

Example: You connect to your VPS through WireGuard or Tailscale and access private monitoring dashboards or databases through that connection.

When to use: When administrative interfaces, internal services, or multiple VPS machines need private connectivity.

These components can be combined, but you do not need all of them. For example, Cloudflare and Nginx may both provide some traffic filtering and proxying, while only Nginx needs to forward requests to your application. An API gateway can also be the reverse proxy, rather than being installed as a separate layer.

## 3. Best practices for a production VPS beyond using a reverse proxy

A reverse proxy is only one part of a production setup. I would prioritize these practices in roughly this order.

1. Network security and least exposure
   - Allow only required inbound ports in both provider and host firewalls.
   - Restrict SSH access where practical and use SSH keys.
   - Do not publish PostgreSQL or internal application ports unnecessarily.
   - Keep administrative dashboards off the public internet unless properly protected.
2. Application and database security
   - Enforce authentication and authorization inside the application.
   - Use separate, least-privileged database credentials for the application.
   - Store secrets outside source control.
   - Validate input and configure safe error handling.
3. Reliable deployment and recovery
   - Deploy reproducibly through Docker and CI/CD.
   - Use health checks and a rollback strategy.
   - Back up PostgreSQL regularly and test restoring the backups.
   - Keep persistent database data separate from disposable application containers.
4. Monitoring and observability
   - Monitor CPU, memory, disk usage, and network availability.
   - Collect application and reverse-proxy logs.
   - Track errors and latency, and configure alerts.
   - Monitor backup success and disk capacity.
5. HTTPS and edge protection
   - Use valid TLS certificates and automate renewal.
   - Consider a CDN/WAF such as Cloudflare if its capabilities fit your application.
   - Configure rate limiting where appropriate.
   - If using an external proxy, configure trusted proxy headers correctly so the application does not blindly trust client-supplied IP or protocol information.

## 4. What I would use for your VPS

Given your goal of deploying multiple side projects cost-effectively, I would start with a relatively simple architecture.

Internet

Cloudflare — optional

DNS, proxying, CDN and WAF features

Nginx or Caddy

Reverse proxy and HTTPS

Docker application network

Next.js / NestJS / background workers

PostgreSQL

Private network; persistent storage

Cloudflare is optional. If you use its proxy and WAF features, configure the origin firewall carefully so clients cannot simply bypass Cloudflare and connect directly to your VPS.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://developers.cloudflare.com\&sz=32)

Cloudflare Web Application Firewall (WAF) docs

+1



My practical recommendations:

- Start with Nginx or Caddy, not an API gateway. Both can handle reverse proxying; Caddy is worth considering if you prefer simpler automatic HTTPS configuration.
- Use Docker networking to keep application and database ports private.
- Add Cloudflare if you want its DNS, CDN, or security features.
- Add an API gateway only when you have a real API-management need, such as multiple independently managed APIs, consumer-specific quotas, or centralized API-key policies.
- Build monitoring, automated backups, and tested recovery procedures into the deployment rather than treating them as optional extras.

For a single VPS running a few applications, an API gateway is usually unnecessary overhead. Nginx or Caddy plus sensible network isolation, application security, backups, and monitoring is a sufficient starting point.

For reference, the official [NGINX reverse proxy documentation](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy) explains request forwarding, and the [Kong Gateway documentation](https://developer.konghq.com/gateway/) explains the additional capabilities of an API gateway.