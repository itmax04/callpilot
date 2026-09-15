#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r azure/requirements.txt
cp azure/local.settings.example.json azure/local.settings.json
printf '%s\n' 'Заполните секреты в azure/local.settings.json только локально; файл не коммитьте.'
