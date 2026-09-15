#!/usr/bin/env bash
set -euo pipefail
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP explicitly}"
: "${LOCATION:=westeurope}"
az deployment group create --resource-group "$RESOURCE_GROUP" --name callpilot --template-file azure/main.bicep --parameters location="$LOCATION"
APP_NAME="$(az deployment group show --resource-group "$RESOURCE_GROUP" --name callpilot --query properties.outputs.functionAppName.value -o tsv)"
func azure functionapp publish "$APP_NAME" --python
