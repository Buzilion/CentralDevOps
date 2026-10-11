# Task 04 — Refactor configuration into roles and a validated template

## Outcome

Organize related baseline automation into a focused role and render one reviewed configuration file with explicit permissions and a validated, change-triggered service action where appropriate.

## Prerequisites

- Read [Lesson 05 — Roles, templates, and reusable configuration](../lessons/05-roles-templates-and-reusable-configuration.md).
- Complete Task 03 and have a known desired configuration from the baseline matrix.
- Use a disposable host for a first service reload/restart test.

## Procedure

1. Move related tasks into a role with conventional `defaults`, `tasks`, `handlers`, and `templates` directories. Keep the top-level playbook focused on host selection, global policy, and role order.
2. Put safe, overridable role defaults in `defaults/main.yml`. Place environment choices in the appropriate group variables. Add no implicit secret, open port, user, or service policy.
3. Select a non-critical configuration file the automation is approved to own. Use a drop-in location when supported rather than overwriting a package-managed file. If no appropriate file exists, practice using a disposable host; do not invent a production setting.
4. Render the file through `ansible.builtin.template`. Set owner, group, and quoted mode explicitly. Use the actual service's documented validation command with the module's `validate` option when available.
5. Notify a handler only when the rendered file changes. Confirm the service supports the selected reload or restart and understand its impact. Do not manage production SSH or firewall templates until their complete recovery sequence has been rehearsed.
6. Check the rendered output on the test host, verify file ownership/mode, and observe whether a second run avoids an unnecessary reload.
7. Review role behavior and test it with the same inventory and variables as the top-level playbook.

## Acceptance criteria

- [ ] The role has a single understandable responsibility and is invoked explicitly from a playbook.
- [ ] Defaults and environment-specific variables are separated and documented.
- [ ] The template contains no plaintext secret and states destination ownership and permissions.
- [ ] Candidate configuration is validated before replacement where the service supports it.
- [ ] Handler action is tied to an actual change and behaves correctly on the test host.
- [ ] A second run produces no unexplained file changes or unnecessary service reloads.
- [ ] The role has an explicit supported-platform assumption and does not alter unrelated configuration.

## Deliverable

A focused role with its template and handler plus sanitized first-run and repeat-run evidence. If a production service file is not safe to test, keep the demonstration on the disposable host and document the production prerequisite.
