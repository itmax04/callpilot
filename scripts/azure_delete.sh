#!/usr/bin/env bash
set -euo pipefail
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP explicitly; deletion is irreversible}"
az group delete --name "$RESOURCE_GROUP" --yes --no-wait
