#!/usr/bin/env bash
# Build the single image in ACR and deploy it to Azure Container Apps.
# Safe to re-run: creates the identity/app on first run, updates them after.
#
#   scripts/azure/deploy.sh            # build + deploy current commit
#   SKIP_BUILD=1 TAG=abc1234 scripts/azure/deploy.sh   # redeploy/roll back an existing tag
#
# App settings come from the environment, falling back to backend/.env:
#   SEC_CONTACT_EMAIL, OPENAI_API_KEY (stored as a Container App secret), OPENAI_MODEL
set -euo pipefail

SUBSCRIPTION="${SUBSCRIPTION:-d4ccf8cd-6f07-4360-b397-ca03b163ddf5}"   # Predir-AI
RESOURCE_GROUP="${RESOURCE_GROUP:-Vault}"
ACR_NAME="${ACR_NAME:-vaultoperations}"
ENVIRONMENT="${ENVIRONMENT:-vault-container-env}"
APP_NAME="${APP_NAME:-stockbrief}"
IMAGE_REPO="${IMAGE_REPO:-stockbrief}"
IDENTITY_NAME="${IDENTITY_NAME:-stockbrief-pull}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="$REPO_ROOT/backend/.env"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# Read KEY from the environment, else from backend/.env (without sourcing it).
setting() {
  local key="$1" val="${!1:-}"
  if [[ -z "$val" && -f "$ENV_FILE" ]]; then
    val="$(grep -E "^${key}=" "$ENV_FILE" | tail -1 | cut -d= -f2- || true)"
    val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
  fi
  printf '%s' "$val"
}

SEC_CONTACT_EMAIL="$(setting SEC_CONTACT_EMAIL)"
OPENAI_API_KEY="$(setting OPENAI_API_KEY)"
OPENAI_MODEL="$(setting OPENAI_MODEL)"
OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o-mini}"
[[ -n "$SEC_CONTACT_EMAIL" ]] || die "SEC_CONTACT_EMAIL is not set (env or backend/.env)"
[[ -n "$OPENAI_API_KEY" ]] || die "OPENAI_API_KEY is not set (env or backend/.env)"

command -v az >/dev/null || die "Azure CLI not found"
az account set --subscription "$SUBSCRIPTION"

# Immutable tag per commit; uncommitted builds get a -dirty-<time> suffix so they never
# overwrite the tag of a real commit.
if [[ -z "${TAG:-}" ]]; then
  TAG="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
  if [[ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]]; then
    TAG="$TAG-dirty-$(date +%Y%m%d%H%M%S)"
  fi
fi
ACR_SERVER="$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)"
IMAGE="$ACR_SERVER/$IMAGE_REPO:$TAG"

if [[ -z "${SKIP_BUILD:-}" ]]; then
  # Builds in Azure as linux/amd64, so this works from Apple Silicon without buildx.
  log "Building $IMAGE in ACR"
  az acr build --registry "$ACR_NAME" --image "$IMAGE_REPO:$TAG" \
    --platform linux/amd64 "$REPO_ROOT"
else
  log "Skipping build, deploying existing $IMAGE"
  az acr repository show -n "$ACR_NAME" --image "$IMAGE_REPO:$TAG" >/dev/null \
    || die "tag $TAG not found in $ACR_NAME/$IMAGE_REPO"
fi

# Pull with a managed identity instead of the registry admin password.
log "Ensuring managed identity $IDENTITY_NAME has AcrPull"
if ! az identity show -g "$RESOURCE_GROUP" -n "$IDENTITY_NAME" >/dev/null 2>&1; then
  az identity create -g "$RESOURCE_GROUP" -n "$IDENTITY_NAME" >/dev/null
fi
IDENTITY_ID="$(az identity show -g "$RESOURCE_GROUP" -n "$IDENTITY_NAME" --query id -o tsv)"
PRINCIPAL_ID="$(az identity show -g "$RESOURCE_GROUP" -n "$IDENTITY_NAME" --query principalId -o tsv)"
ACR_ID="$(az acr show -n "$ACR_NAME" --query id -o tsv)"
if [[ -z "$(az role assignment list --assignee "$PRINCIPAL_ID" --scope "$ACR_ID" --role AcrPull --query '[0].id' -o tsv 2>/dev/null)" ]]; then
  # (list errors for a brand-new identity not yet in Graph; treat that as "no assignment")
  az role assignment create --assignee-object-id "$PRINCIPAL_ID" \
    --assignee-principal-type ServicePrincipal --role AcrPull --scope "$ACR_ID" >/dev/null
  log "Waiting 60s for the role assignment to propagate"
  sleep 60
fi

ENV_VARS=(
  "SEC_CONTACT_EMAIL=$SEC_CONTACT_EMAIL"
  "OPENAI_MODEL=$OPENAI_MODEL"
  "OPENAI_API_KEY=secretref:openai-api-key"
)

if ! az containerapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" >/dev/null 2>&1; then
  log "Creating container app $APP_NAME in $ENVIRONMENT"
  # One replica for v0: caches are in-memory and the SEC rate limiter is per process.
  az containerapp create -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --environment "$ENVIRONMENT" \
    --image "$IMAGE" \
    --user-assigned "$IDENTITY_ID" \
    --registry-server "$ACR_SERVER" --registry-identity "$IDENTITY_ID" \
    --ingress external --target-port 8000 \
    --cpu 0.5 --memory 1.0Gi \
    --min-replicas 1 --max-replicas 1 \
    --secrets "openai-api-key=$OPENAI_API_KEY" \
    --env-vars "${ENV_VARS[@]}" \
    --output none
else
  log "Updating container app $APP_NAME to $TAG"
  az containerapp secret set -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --secrets "openai-api-key=$OPENAI_API_KEY" --output none
  az containerapp update -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --image "$IMAGE" \
    --set-env-vars "${ENV_VARS[@]}" \
    --output none
fi

# The old revision keeps serving until the new one is ready, so /health alone can
# pass against the previous image. Wait for the new revision to become ready first.
log "Waiting for the new revision to become ready"
ready=""
for _ in $(seq 1 40); do
  read -r latest latest_ready < <(az containerapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" \
    --query "[properties.latestRevisionName, properties.latestReadyRevisionName]" -o tsv | tr '\n' ' ')
  if [[ -n "$latest" && "$latest" == "$latest_ready" ]]; then ready=1; break; fi
  sleep 10
done
[[ -n "$ready" ]] || die "revision $latest not ready after ~7 minutes; check: az containerapp revision list -g $RESOURCE_GROUP -n $APP_NAME -o table"

FQDN="$(az containerapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" --query properties.configuration.ingress.fqdn -o tsv)"
log "Checking https://$FQDN/health"
for _ in $(seq 1 20); do
  if curl -fsS "https://$FQDN/health" >/dev/null 2>&1; then
    log "Deployed $IMAGE → https://$FQDN"
    exit 0
  fi
  sleep 6
done
die "deployed $IMAGE but /health did not respond; check: az containerapp logs show -g $RESOURCE_GROUP -n $APP_NAME"
