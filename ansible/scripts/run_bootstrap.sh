#!/usr/bin/env bash
set -euo pipefail
umask 077

error() {
  printf '::error::%s\n' "$1" >&2
  exit 1
}

warning() {
  printf '::warning::%s\n' "$1" >&2
}

require_value() {
  local name="$1"
  if [[ ! -v $name ]]; then
    error "Required protected Environment configuration is missing: $name."
  fi
  local value="${!name}"
  if [[ -z "$value" ]]; then
    error "Required protected Environment configuration is missing: $name."
  fi
}

has_service() {
  case ",${BOOTSTRAP_EFFECTIVE_SERVICES:-}," in
    *",$1,"*) return 0 ;;
    *) return 1 ;;
  esac
}

validate_image_digest() {
  local name="$1"
  local image=""
  if [[ -v $name ]]; then
    image="${!name}"
  fi
  require_value "$name"
  if [[ ! "$image" =~ ^[A-Za-z0-9][A-Za-z0-9._/:@-]*@sha256:[0-9a-f]{64}$ ]]; then
    error "$name must be an approved immutable image reference ending in @sha256:<64 lowercase hex characters>."
  fi
}

validate_package_version() {
  local name="$1"
  local version=""
  if [[ -v $name ]]; then
    version="${!name}"
  fi
  require_value "$name"
  if [[ ! "$version" =~ ^[A-Za-z0-9.+:~_-]+$ ]]; then
    error "$name contains unsupported characters."
  fi
}

require_single_line() {
  local name="$1"
  local value=""
  if [[ -v $name ]]; then
    value="${!name}"
  fi
  if [[ "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
    error "$name must be a single-line value."
  fi
}

validate_https_endpoint() {
  local name="$1"
  local value=""
  local pattern='^https://[A-Za-z0-9._~:/?=&%+-]+$'
  if [[ -v $name ]]; then
    value="${!name}"
  fi
  require_value "$name"
  if [[ ! "$value" =~ $pattern ]]; then
    error "$name must be an HTTPS endpoint without shell or configuration syntax."
  fi
}

if [[ "${BOOTSTRAP_MODE:-}" != "validate" && "${BOOTSTRAP_MODE:-}" != "apply" ]]; then
  error "Execution mode must be validate or apply."
fi

require_value BOOTSTRAP_INVENTORY
require_value BOOTSTRAP_TARGET_HOST
require_value BOOTSTRAP_USER
require_value ANSIBLE_HOST
require_value BOOTSTRAP_HOST_ID
require_value BOOTSTRAP_APPLICATION_ENVIRONMENT
require_value BOOTSTRAP_KNOWN_HOSTS
require_value DEPLOY_PRIVATE_KEY
require_value DEPLOY_PUBLIC_KEY
if [[ -n "${BOOTSTRAP_PASSWORD:-}" ]]; then
  require_single_line BOOTSTRAP_PASSWORD
fi

if [[ "${BOOTSTRAP_SHARED_HOST_COLLISION:-false}" == "true" \
  && "${BOOTSTRAP_SHARED_HOST_APPROVED:-}" != "true" ]]; then
  error "Aliases share a verified physical host; set BOOTSTRAP_SHARED_HOST_APPROVED=true in the selected protected Environment after reviewing the shared-host policy."
fi

if [[ "$BOOTSTRAP_MODE" == "apply" ]]; then
  if [[ "${SUMOPOD_FIREWALL_REVIEWED:-}" != "true" ]]; then
    error "Apply requires a completed manual Sumopod firewall review (SUMOPOD_FIREWALL_REVIEWED=true)."
  fi
  if [[ "${SUMOPOD_SSH_SOURCE_RESTRICTED:-}" != "true" \
    && "${SUMOPOD_PUBLIC_SSH_EXCEPTION_APPROVED:-}" != "true" ]]; then
    error "Apply requires a restricted Sumopod SSH source or an owner-approved public SSH exception."
  fi
elif [[ "${SUMOPOD_FIREWALL_REVIEWED:-}" != "true" ]]; then
  warning "Sumopod firewall policy is a manual boundary and has not been attested in this Environment."
fi

if has_service docker; then
  validate_package_version BOOTSTRAP_DOCKER_CE_PACKAGE_VERSION
  validate_package_version BOOTSTRAP_DOCKER_CLI_PACKAGE_VERSION
  validate_package_version BOOTSTRAP_CONTAINERD_PACKAGE_VERSION
  validate_package_version BOOTSTRAP_BUILDX_PACKAGE_VERSION
  validate_package_version BOOTSTRAP_COMPOSE_PACKAGE_VERSION
fi

if has_service nginx; then
  validate_image_digest BOOTSTRAP_NGINX_IMAGE
  validate_image_digest BOOTSTRAP_CERTBOT_IMAGE
  require_value BOOTSTRAP_ROUTE_FQDN
fi

if has_service postgresql; then
  validate_image_digest BOOTSTRAP_POSTGRES_IMAGE
  validate_image_digest BOOTSTRAP_AWS_CLI_IMAGE
  require_value BOOTSTRAP_POSTGRES_DATA_DIRECTORY
  if [[ ! "$BOOTSTRAP_POSTGRES_DATA_DIRECTORY" =~ ^/[A-Za-z0-9._/-]+$ \
    || "$BOOTSTRAP_POSTGRES_DATA_DIRECTORY" == *".."* ]]; then
    error "BOOTSTRAP_POSTGRES_DATA_DIRECTORY must be a safe absolute path approved for the pinned image."
  fi
  require_value BOOTSTRAP_POSTGRESQL_DB_PASSWORD
  require_single_line BOOTSTRAP_POSTGRESQL_DB_PASSWORD
  require_value BOOTSTRAP_POSTGRESQL_S3_ACCESS_KEY_ID
  require_value BOOTSTRAP_POSTGRESQL_S3_SECRET_ACCESS_KEY
  require_value BOOTSTRAP_POSTGRESQL_S3_RESTORE_ACCESS_KEY_ID
  require_value BOOTSTRAP_POSTGRESQL_S3_RESTORE_SECRET_ACCESS_KEY
  for name in \
    BOOTSTRAP_POSTGRESQL_S3_ACCESS_KEY_ID \
    BOOTSTRAP_POSTGRESQL_S3_SECRET_ACCESS_KEY \
    BOOTSTRAP_POSTGRESQL_S3_RESTORE_ACCESS_KEY_ID \
    BOOTSTRAP_POSTGRESQL_S3_RESTORE_SECRET_ACCESS_KEY; do
    require_single_line "$name"
    if [[ ! "${!name}" =~ ^[A-Za-z0-9+/=_-]+$ ]]; then
      error "$name contains unsupported characters for the protected AWS environment file."
    fi
  done
  if [[ "${BOOTSTRAP_POSTGRES_BACKUP_POLICY_VERIFIED:-}" != "true" ]]; then
    error "PostgreSQL requires verified S3 encryption, versioning, lifecycle, credential scope, and recovery policy before any changes."
  fi
fi

if has_service alloy; then
  validate_package_version BOOTSTRAP_ALLOY_PACKAGE_VERSION
  validate_https_endpoint GRAFANA_PROMETHEUS_URL
  require_value GRAFANA_PROMETHEUS_USER
  validate_https_endpoint GRAFANA_LOKI_URL
  require_value GRAFANA_LOKI_USER
  require_value GRAFANA_TEMPO_URL
  tempo_url_pattern='^([A-Za-z0-9.-]+:[0-9]+|https://[A-Za-z0-9._~:/?=&%+-]+)$'
  if [[ ! "$GRAFANA_TEMPO_URL" =~ $tempo_url_pattern ]]; then
    error "GRAFANA_TEMPO_URL must be a host:port or HTTPS endpoint."
  fi
  require_value GRAFANA_TEMPO_USER
  require_value GRAFANA_OTLP_ENDPOINT
  require_value GRAFANA_INSTANCE_ID
  require_value GRAFANA_API_TOKEN
  for name in GRAFANA_PROMETHEUS_USER GRAFANA_LOKI_USER GRAFANA_TEMPO_USER GRAFANA_INSTANCE_ID; do
    if [[ ! "${!name}" =~ ^[A-Za-z0-9._-]+$ ]]; then
      error "$name contains unsupported characters."
    fi
  done
  endpoint_pattern='^https://[A-Za-z0-9._~:/?=&%+-]+$'
  if [[ ! "$GRAFANA_OTLP_ENDPOINT" =~ $endpoint_pattern ]]; then
    error "GRAFANA_OTLP_ENDPOINT must be an HTTPS endpoint without shell or configuration syntax."
  fi
  if [[ "$GRAFANA_API_TOKEN" == *$'\n'* || "$GRAFANA_API_TOKEN" == *$'\r'* ]]; then
    error "GRAFANA_API_TOKEN must be a single-line value."
  fi
  if [[ "${BOOTSTRAP_ALLOY_DELIVERY_VERIFIED:-}" != "true" ]]; then
    error "Alloy requires approved Grafana Cloud configuration and a verified delivery test before any changes."
  fi
fi

WORK_DIR="$(mktemp -d "$RUNNER_TEMP/bootstrap-vps.XXXXXX")"
chmod 700 "$WORK_DIR"
REPORT_PATH="$RUNNER_TEMP/bootstrap-report.json"
ANSIBLE_LOG="$RUNNER_TEMP/bootstrap-ansible.log"
DEPLOY_KEY_FILE="$WORK_DIR/deploy.key"
DEPLOY_PUBLIC_KEY_FILE="$WORK_DIR/deploy.pub"
DEPLOY_DERIVED_PUBLIC_KEY_FILE="$WORK_DIR/deploy-derived.pub"
KNOWN_HOSTS_FILE="$WORK_DIR/known_hosts"
ANSIBLE_VARS_FILE="$WORK_DIR/ansible-vars.json"
CONNECTION_INVENTORY_FILE="$WORK_DIR/connection-inventory.yml"

cleanup() {
  rm -f \
    "$DEPLOY_KEY_FILE" \
    "$DEPLOY_PUBLIC_KEY_FILE" \
    "$DEPLOY_DERIVED_PUBLIC_KEY_FILE" \
    "$KNOWN_HOSTS_FILE" \
    "$ANSIBLE_VARS_FILE" \
    "$CONNECTION_INVENTORY_FILE"
  rmdir "$WORK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

printf '%s\n' "$DEPLOY_PRIVATE_KEY" > "$DEPLOY_KEY_FILE"
printf '%s\n' "$DEPLOY_PUBLIC_KEY" > "$DEPLOY_PUBLIC_KEY_FILE"
printf '%s\n' "$BOOTSTRAP_KNOWN_HOSTS" > "$KNOWN_HOSTS_FILE"

derive_public_key() {
  local private_key_file="$1"
  local derived_public_key_file="$2"
  if ! ssh-keygen -y -P '' -f "$private_key_file" \
    > "$derived_public_key_file" 2>/dev/null; then
    return 1
  fi
}

key_fingerprint() {
  local public_key_file="$1"
  local fingerprint_line fingerprint algorithm
  fingerprint_line="$(ssh-keygen -lf "$public_key_file" 2>/dev/null)" || return 1
  fingerprint="$(printf '%s\n' "$fingerprint_line" | awk '{print $2}')"
  algorithm="$(printf '%s\n' "$fingerprint_line" | sed -n 's/.*(\([^)]*\))$/\1/p')"
  printf '%s|%s' "$fingerprint" "$algorithm"
}

derive_public_key "$DEPLOY_KEY_FILE" "$DEPLOY_DERIVED_PUBLIC_KEY_FILE" \
  || error "The deploy private key is invalid or passphrase-protected."

deploy_private_fingerprint="$(key_fingerprint "$DEPLOY_DERIVED_PUBLIC_KEY_FILE")" \
  || error "The deploy private key could not be fingerprinted."
deploy_public_fingerprint="$(key_fingerprint "$DEPLOY_PUBLIC_KEY_FILE")" \
  || error "The deploy public-key variable is invalid."

if [[ "$deploy_private_fingerprint" != "$deploy_public_fingerprint" ]]; then
  error "The deploy private key does not match its protected public-key variable."
fi
if [[ "$deploy_private_fingerprint" != *'|ED25519' ]]; then
  error "The deploy key must be Ed25519."
fi

if ! ssh-keygen -F "$ANSIBLE_HOST" -f "$KNOWN_HOSTS_FILE" >/dev/null 2>&1; then
  error "The protected known-hosts value does not pin the selected VPS address."
fi

password_ssh_options=(
  -F /dev/null
  -o StrictHostKeyChecking=yes
  -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE"
  -o PubkeyAuthentication=no
  -o PasswordAuthentication=yes
  -o KbdInteractiveAuthentication=yes
  -o PreferredAuthentications=password,keyboard-interactive
  -o ConnectTimeout=15
)

deploy_key_ssh_options=(
  -F /dev/null
  -o BatchMode=yes
  -o IdentitiesOnly=yes
  -o StrictHostKeyChecking=yes
  -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE"
  -o PasswordAuthentication=no
  -o KbdInteractiveAuthentication=no
  -o PreferredAuthentications=publickey
  -o ConnectTimeout=15
)

BOOTSTRAP_CONNECTION_MODE=""
BOOTSTRAP_CONNECTION_USER=""
if [[ -n "${BOOTSTRAP_PASSWORD:-}" ]]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    error "sshpass is required to use the protected bootstrap password."
  fi
  if SSHPASS="$BOOTSTRAP_PASSWORD" sshpass -e ssh "${password_ssh_options[@]}" \
    "$BOOTSTRAP_USER@$ANSIBLE_HOST" true >/dev/null 2>&1; then
    BOOTSTRAP_CONNECTION_MODE="password"
    BOOTSTRAP_CONNECTION_USER="$BOOTSTRAP_USER"
  else
    warning "Bootstrap password SSH did not succeed; checking deploy-key access for an already-bootstrapped VPS."
  fi
fi

if [[ -z "$BOOTSTRAP_CONNECTION_MODE" ]]; then
  if ssh "${deploy_key_ssh_options[@]}" -i "$DEPLOY_KEY_FILE" \
    "deploy@$ANSIBLE_HOST" true >/dev/null 2>&1; then
    BOOTSTRAP_CONNECTION_MODE="deploy-key"
    BOOTSTRAP_CONNECTION_USER="deploy"
  else
    error "Pinned SSH failed. Configure the per-host bootstrap password secret for initial access, or verify deploy-key access for an already-bootstrapped VPS; no remote changes were made."
  fi
fi

export DEPLOY_KEY_FILE="$DEPLOY_KEY_FILE"
export KNOWN_HOSTS_FILE="$KNOWN_HOSTS_FILE"
export REPORT_PATH="$REPORT_PATH"
export BOOTSTRAP_CONNECTION_MODE
export BOOTSTRAP_CONNECTION_USER
export CONNECTION_INVENTORY_FILE
BOOTSTRAP_SSH_COMMON_ARGS="-o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KNOWN_HOSTS_FILE -o PubkeyAuthentication=no -o PasswordAuthentication=yes -o KbdInteractiveAuthentication=yes -o PreferredAuthentications=password,keyboard-interactive"
DEPLOY_SSH_COMMON_ARGS="-o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KNOWN_HOSTS_FILE -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o PreferredAuthentications=publickey"
if [[ "$BOOTSTRAP_CONNECTION_MODE" == "deploy-key" ]]; then
  BOOTSTRAP_SSH_COMMON_ARGS="$DEPLOY_SSH_COMMON_ARGS"
fi
export BOOTSTRAP_SSH_COMMON_ARGS
export DEPLOY_SSH_COMMON_ARGS

python - "$ANSIBLE_VARS_FILE" <<'PY'
import json
import os
import sys

def boolean(name):
    return os.environ.get(name, "").strip().lower() == "true"

requested_services = [
    service
    for service in os.environ.get("BOOTSTRAP_REQUESTED_SERVICES", "").split(",")
    if service
]
postgresql_selected = "postgresql" in requested_services

variables = {
    "bootstrap_mode": os.environ["BOOTSTRAP_MODE"],
    "bootstrap_inventory": os.environ["BOOTSTRAP_INVENTORY"],
    "bootstrap_target_host": os.environ["BOOTSTRAP_TARGET_HOST"],
    "bootstrap_user": os.environ["BOOTSTRAP_USER"],
    "bootstrap_connection_mode": os.environ["BOOTSTRAP_CONNECTION_MODE"],
    "bootstrap_connection_user": os.environ["BOOTSTRAP_CONNECTION_USER"],
    "bootstrap_ssh_common_args": os.environ["BOOTSTRAP_SSH_COMMON_ARGS"],
    "bootstrap_deploy_ssh_common_args": os.environ["DEPLOY_SSH_COMMON_ARGS"],
    "bootstrap_host_id": os.environ["BOOTSTRAP_HOST_ID"],
    "bootstrap_environment": os.environ["BOOTSTRAP_ENVIRONMENT"],
    "bootstrap_application_environment": os.environ["BOOTSTRAP_APPLICATION_ENVIRONMENT"],
    "bootstrap_application": os.environ["BOOTSTRAP_APPLICATION"],
    "bootstrap_route_fqdn": os.environ.get("BOOTSTRAP_ROUTE_FQDN", ""),
    "bootstrap_requested_services": requested_services,
    "bootstrap_effective_services": json.loads(
        os.environ["BOOTSTRAP_EFFECTIVE_SERVICES_JSON"]
    ),
    "bootstrap_shared_host_collision": boolean("BOOTSTRAP_SHARED_HOST_COLLISION"),
    "bootstrap_shared_host_approved": boolean("BOOTSTRAP_SHARED_HOST_APPROVED"),
    "bootstrap_provider_firewall_reviewed": boolean("SUMOPOD_FIREWALL_REVIEWED"),
    "bootstrap_sumopod_ssh_source_restricted": boolean("SUMOPOD_SSH_SOURCE_RESTRICTED"),
    "bootstrap_public_ssh_exception_approved": boolean(
        "SUMOPOD_PUBLIC_SSH_EXCEPTION_APPROVED"
    ),
    "bootstrap_deploy_user": "deploy",
    "bootstrap_deploy_public_key": os.environ["DEPLOY_PUBLIC_KEY"],
    "bootstrap_deploy_private_key_file": os.environ["DEPLOY_KEY_FILE"],
    "bootstrap_known_hosts_file": os.environ["KNOWN_HOSTS_FILE"],
    "bootstrap_report_path": os.environ["REPORT_PATH"],
    "bootstrap_docker_ce_package_version": os.environ.get(
        "BOOTSTRAP_DOCKER_CE_PACKAGE_VERSION", ""
    ),
    "bootstrap_docker_cli_package_version": os.environ.get(
        "BOOTSTRAP_DOCKER_CLI_PACKAGE_VERSION", ""
    ),
    "bootstrap_containerd_package_version": os.environ.get(
        "BOOTSTRAP_CONTAINERD_PACKAGE_VERSION", ""
    ),
    "bootstrap_buildx_package_version": os.environ.get(
        "BOOTSTRAP_BUILDX_PACKAGE_VERSION", ""
    ),
    "bootstrap_compose_package_version": os.environ.get(
        "BOOTSTRAP_COMPOSE_PACKAGE_VERSION", ""
    ),
    "bootstrap_nginx_image": os.environ.get("BOOTSTRAP_NGINX_IMAGE", ""),
    "bootstrap_certbot_image": os.environ.get("BOOTSTRAP_CERTBOT_IMAGE", ""),
    "bootstrap_postgres_image": os.environ.get("BOOTSTRAP_POSTGRES_IMAGE", ""),
    "bootstrap_aws_cli_image": os.environ.get("BOOTSTRAP_AWS_CLI_IMAGE", ""),
    "bootstrap_postgresql_data_directory": os.environ.get(
        "BOOTSTRAP_POSTGRES_DATA_DIRECTORY", ""
    ),
    "bootstrap_postgresql_db_password": os.environ.get(
        "BOOTSTRAP_POSTGRESQL_DB_PASSWORD", ""
    )
    if postgresql_selected
    else "",
    "bootstrap_s3_access_key_id": os.environ.get(
        "BOOTSTRAP_POSTGRESQL_S3_ACCESS_KEY_ID", ""
    )
    if postgresql_selected
    else "",
    "bootstrap_s3_secret_access_key": os.environ.get(
        "BOOTSTRAP_POSTGRESQL_S3_SECRET_ACCESS_KEY", ""
    )
    if postgresql_selected
    else "",
    "bootstrap_s3_restore_access_key_id": os.environ.get(
        "BOOTSTRAP_POSTGRESQL_S3_RESTORE_ACCESS_KEY_ID", ""
    )
    if postgresql_selected
    else "",
    "bootstrap_s3_restore_secret_access_key": os.environ.get(
        "BOOTSTRAP_POSTGRESQL_S3_RESTORE_SECRET_ACCESS_KEY", ""
    )
    if postgresql_selected
    else "",
    "bootstrap_postgres_backup_policy_verified": boolean(
        "BOOTSTRAP_POSTGRES_BACKUP_POLICY_VERIFIED"
    )
    if postgresql_selected
    else False,
    "bootstrap_alloy_package_version": os.environ.get(
        "BOOTSTRAP_ALLOY_PACKAGE_VERSION", ""
    ),
    "bootstrap_alloy_delivery_verified": boolean(
        "BOOTSTRAP_ALLOY_DELIVERY_VERIFIED"
    ),
    "bootstrap_grafana_prometheus_url": os.environ.get("GRAFANA_PROMETHEUS_URL", ""),
    "bootstrap_grafana_prometheus_user": os.environ.get(
        "GRAFANA_PROMETHEUS_USER", ""
    ),
    "bootstrap_grafana_loki_url": os.environ.get("GRAFANA_LOKI_URL", ""),
    "bootstrap_grafana_loki_user": os.environ.get("GRAFANA_LOKI_USER", ""),
    "bootstrap_grafana_tempo_url": os.environ.get("GRAFANA_TEMPO_URL", ""),
    "bootstrap_grafana_tempo_user": os.environ.get("GRAFANA_TEMPO_USER", ""),
    "bootstrap_grafana_otlp_endpoint": os.environ.get("GRAFANA_OTLP_ENDPOINT", ""),
    "bootstrap_grafana_instance_id": os.environ.get("GRAFANA_INSTANCE_ID", ""),
    "bootstrap_grafana_api_token": os.environ.get("GRAFANA_API_TOKEN", ""),
}

with open(sys.argv[1], "w", encoding="utf-8") as output_file:
    json.dump(variables, output_file, separators=(",", ":"))
os.chmod(sys.argv[1], 0o600)
PY

python - "$CONNECTION_INVENTORY_FILE" <<'PY'
import json
import os
import sys

connection_variables = {}
if os.environ["BOOTSTRAP_CONNECTION_MODE"] == "password":
    connection_variables["ansible_password"] = os.environ["BOOTSTRAP_PASSWORD"]

inventory = {
    "all": {
        "hosts": {
            os.environ["BOOTSTRAP_TARGET_HOST"]: connection_variables,
        }
    }
}
with open(sys.argv[1], "w", encoding="utf-8") as output_file:
    json.dump(inventory, output_file, separators=(",", ":"))
os.chmod(sys.argv[1], 0o600)
PY

export ANSIBLE_CONFIG="$GITHUB_WORKSPACE/ansible/ansible.cfg"
export ANSIBLE_HOST_KEY_CHECKING=True

ansible_arguments=(
  --inventory "$BOOTSTRAP_INVENTORY" \
  --inventory "$CONNECTION_INVENTORY_FILE" \
  --limit "$BOOTSTRAP_TARGET_HOST" \
  --user "$BOOTSTRAP_CONNECTION_USER" \
  --extra-vars "@$ANSIBLE_VARS_FILE"
)
if [[ "$BOOTSTRAP_CONNECTION_MODE" == "deploy-key" ]]; then
  ansible_arguments+=(--private-key "$DEPLOY_KEY_FILE")
fi

ansible-playbook "${ansible_arguments[@]}" \
  ansible/playbooks/bootstrap.yml \
  2>&1 | tee "$ANSIBLE_LOG"

pending_reboot="unknown"
if grep -q 'BOOTSTRAP_PENDING_REBOOT=true' "$ANSIBLE_LOG"; then
  pending_reboot="true"
elif grep -q 'BOOTSTRAP_PENDING_REBOOT=false' "$ANSIBLE_LOG"; then
  pending_reboot="false"
fi
printf 'pending_reboot=%s\n' "$pending_reboot" >> "$GITHUB_OUTPUT"
