#!/usr/bin/env bash
# Usage: RESUME_KEY=... ./normalize.sh
curl -s -X POST https://www.resumereaderapi.com/api/normalize_skills.php \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"$RESUME_KEY\",\"skills\":[\"JS\",\"Python 3.11\",\"K8s\",\"MS Excel\"]}"
