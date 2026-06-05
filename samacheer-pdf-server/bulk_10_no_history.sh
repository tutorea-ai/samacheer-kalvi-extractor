#!/bin/bash
DISCIPLINES=("geography" "civics" "economics")
BASE_URL="http://localhost:8000/api/generate"

for DISCIPLINE in "${DISCIPLINES[@]}"; do
  echo "🚀 Generating: Class 10 | $DISCIPLINE"
  curl -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"class_num\": 10, \"term\": 0, \"medium\": \"english\",
      \"subject\": \"SocialScience\", \"discipline\": \"$DISCIPLINE\",
      \"unit\": 1, \"lesson_choice\": 1, \"mode\": \"discipline\",
      \"output_format\": \"html\", \"force\": true
    }"
  echo ""
  echo "✅ Done: $DISCIPLINE"
  echo "---"
done
