# Production-readiness checklist

Use this as the definition of done rather than considering a successful HTTP response sufficient.

### Security
- [ ] SSH uses keys and root login is appropriately restricted.
- [ ] Firewall allows only necessary inbound traffic.
- [ ] Secrets are not committed to Git or baked into images.
- [ ] Application and database ports are not publicly exposed unnecessarily.
- [ ] Security updates and access reviews have a defined process.

### Deployment
- [ ] Application runs with a pinned, identifiable release.
- [ ] Docker Compose configuration is version-controlled.
- [ ] Application restarts appropriately after a crash or reboot.
- [ ] HTTPS and domain routing work correctly.
- [ ] Failed deployments can be rolled back.

### Reliability
- [ ] Persistent data survives container recreation.
- [ ] Backups run automatically and are stored off-site.
- [ ] A backup has been restored successfully in a test.
- [ ] Disk, memory, and CPU capacity are monitored.
- [ ] Application health and external uptime are checked.

### Operations
- [ ] Logs can be inspected during a failure.
- [ ] Important failures trigger actionable alerts.
- [ ] Ansible can configure a fresh server repeatably.
- [ ] GitHub Actions deploys through restricted credentials.
- [ ] Recovery and deployment procedures are documented.