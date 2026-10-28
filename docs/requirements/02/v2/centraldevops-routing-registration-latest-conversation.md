# CentralDevOps: Routing Registration During Application Deployment

## User question

Where does routing registration (point 4) happen? Does it happen while `deploy.yml` runs in each application repository?

## Answer

Yes. **Routing registration should normally happen as part of each application's `deploy.yml` workflow**, after the application has been deployed and its health check passes. The routing implementation belongs in CentralDevOps, rather than being duplicated across application repositories.

## Deployment flow

1. **Application repository — `deploy.yml`**
   - Manually triggered with the Docker image digest and target environment.
2. **CentralDevOps — shared deployment action**
   - Pull the image, deploy containers, and configure runtime secrets.
3. **Health check**
   - Confirm that the deployed application is healthy.
4. **CentralDevOps — routing registration**
   - Render the Nginx configuration.
   - Validate it using `nginx -t`.
   - Reload Nginx only after validation succeeds.
5. **External verification**
   - Verify the domain and HTTPS endpoint.

The GitHub Actions runner initiates these operations. CentralDevOps logic connects to the VPS—typically over SSH—to update the actual Nginx configuration.

## Responsibility boundaries

| Component | Responsibility |
|---|---|
| Application's `build.yml` | Build and push the Docker image to GHCR. |
| Application's `deploy.yml` | Accept the image digest and environment, then orchestrate deployment. |
| Application deployment configuration | Declare the domain, internal port, service name, and health endpoint. |
| CentralDevOps shared action or script | Implement deployment and routing-registration logic. |
| VPS running Nginx | Host active routing configuration and handle incoming requests. |

## Does routing registration need to run on every deployment?

The workflow can invoke routing registration on every deployment, but the operation should be **idempotent**. If the route already exists and its configuration has not changed, it should not rewrite the configuration or reload Nginx unnecessarily.

For example, the first deployment of `builder.example.com` registers a new route. A later deployment that only changes application code normally leaves that route unchanged.

## Credential consideration

If Nginx runs on a separate proxy VPS, the routing operation must have a secure way to access that server. A composite action cannot automatically access secrets stored exclusively in the CentralDevOps repository. Use an explicit credential-passing strategy or a CentralDevOps reusable workflow for operations that require CentralDevOps-owned secrets.

## Recommendation

Make routing registration a dedicated step within the centralized deployment implementation, invoked by each application's `deploy.yml`. Keep `build.yml` independent of routing because building an image does not mean that the image has been deployed.
