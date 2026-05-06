#!/usr/bin/env bash
set -euo pipefail

uv run --no-dev python manage.py collectstatic --no-input
rsync -r static/ python:/home/vEnhance/applications/list/static
