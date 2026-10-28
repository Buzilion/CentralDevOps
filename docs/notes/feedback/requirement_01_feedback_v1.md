# Requirement Feedback

- Currently, in the first step when try to connect to the new VPS using username and password, if password auth already been disabled, the workflow will result in an error and it will be stopped. Instead of that, please connect to the VPS using the configured private/public key-pair on the Github Environment Secrets/Variables.

- I need a handling and validation logic for a case where in the workflow steps the VPS has already configured the intended service installation/configuration. First, it needs to check whether the service/item exist or not. If not, then install, if yes, then check whether the configuration is like the one intended on the workflow or not. Then, check the item availability to make sure there is no error or misconfiguration.

- Docker and nginx should be an optional services to select just like PostgreSQL or Grafana

# Open decisions answer

1. Currently there are two inventory files on the ansible folder, namely customer-builder-engine and outbound-marketing. 
2. No, the initial bootstrap account will be provided by the VPS provider (usually, the username is ubuntu). The deploy account should be different.
3. The provider name is Sumopod, it's a new startup and I think it doesn't have readily use API to manage the VPS.
4. - S3 endpoint: https://kencana.basic.box.cloudeka.id
   - Region: kencana
   - Bucket name: buz-stg-prod-1-lb4jef
   - Access key ID: BUZ_STG_PROD_1_ID (gh environment variable)
   - Secret access key: BUZ_STG_PROD_1_SECRET (gh environment secret)
5. Configure Alloy to send metrics, logs, and traces to our Grafana Cloud stack. Store the required endpoints and stack identifiers in approved configuration, and keep the API token in a protected GitHub Environment secret—not in workflow-dispatch inputs. Route alerts to email aristaaldo3@gmail.com. Do not configure alert destinations until they’re confirmed.
6. - Application: Customer Builder Engine
   - FQDN: cbe.buzilion.id
   - Upstream: 0.0.0.0:3000 (docker container, no host port provided. Use docker network for routing from Nginx container)
   - Health check endpoint: /api/health
7. Apply package updates that may require a automatic reboot only during night time at 00.00 GMT +8. The workflow must not reboot the host. If an update leaves a reboot pending, report that status and leave the host running. Reboot later only during an approved maintenance window, after the notification sent to email and authorized user triggered reboot workflow for the targeted VPS through GitHub Action.


# Explore more

- The VPS user account, groups, and it's ownership must be defined also as part of the bootstrap configurations. But, I still don't have the picture on what and how to define it.

- Explore more about this gap "**Repository gap:** the currently inspected inventory files contain host aliases and `ansible_host` addresses, but no obvious public FQDN field. Add and validate an explicit hostname field before relying on inventory for TLS and HTTPS checks."
