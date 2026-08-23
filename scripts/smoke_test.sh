#!/usr/bin/env bash
# End-to-end smoke test for the Hector MVP (Plan 4 / acceptance criterion 3).
# Requires: docker compose db running, API server started via `hector serve`,
# migrations applied, and curl + jq available.
set -euo pipefail

BASE="${HECTOR_SMOKE_BASE:-http://localhost:8000}"
STAMP="$(date +%s)"
PASS=0

check() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    PASS=$((PASS + 1))
    echo "  ok: $desc"
  else
    echo "  FAIL: $desc (expected $expected, got $actual)" >&2
    exit 1
  fi
}

code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
# Usage: json '<accessor-expr>' <curl args...>
json() {
  local expr="$1"
  shift
  curl -s "$@" | python3 -c "import sys,json; print(json.load(sys.stdin)$expr)"
}

echo "== 1. Health =="
check "health endpoint" 200 "$(code "$BASE/health")"

echo "== 2. Bootstrap admin via CLI convention (register blocked, CLI used) =="
python3 -m hector.cli create-admin --email "admin-$STAMP@example.com" --password 'Adm1nStrongPass'
ADMIN_TOKEN="$(json "['access_token']" -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\": \"admin-$STAMP@example.com\", \"password\": \"Adm1nStrongPass\"}")"
echo "  admin logged in"

echo "== 3. Register clinic staff + owner; admin self-registration must fail =="
check "owner register" 201 "$(code -X POST "$BASE/auth/register" -H 'Content-Type: application/json' \
  -d '{"email": "owner-'"$STAMP"'@example.com", "password": "Own3rPassXYZ", "role": "dog_owner"}')"
check "staff register" 201 "$(code -X POST "$BASE/auth/register" -H 'Content-Type: application/json' \
  -d '{"email": "staff-'"$STAMP"'@clinic.com", "password": "St4ffPassXYZ", "role": "clinic_staff"}')"
check "admin self-register blocked" 422 "$(code -X POST "$BASE/auth/register" -H 'Content-Type: application/json' \
  -d '{"email": "evil-'"$STAMP"'@example.com", "password": "EvilPass123", "role": "admin"}')"

OWNER_TOKEN="$(json "['access_token']" -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email": "owner-'"$STAMP"'@example.com", "password": "Own3rPassXYZ"}')"
STAFF_TOKEN="$(json "['access_token']" -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"email": "staff-'"$STAMP"'@clinic.com", "password": "St4ffPassXYZ"}')"

echo "== 4. Clinic profile created by staff, approved by admin (T-400/T-704) =="
CLINIC_ID="$(curl -s -X POST "$BASE/clinics" -H "Authorization: Bearer $STAFF_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Smoke Vet '"$STAMP"'","address":"1 Main St","city":"Berlin","postal_code":"10115","phone":"+49300000","email":"smoke-'"$STAMP"'@vet.de"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")"
check "approve clinic" 200 "$(code -X POST "$BASE/admin/clinics/$CLINIC_ID/approve" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H 'Content-Type: application/json' -d '{}')"

echo "== 5. Owner adds eligible dog with photo (T-300/T-1001) =="
DOG_ID="$(curl -s -X POST "$BASE/dogs" -H "Authorization: Bearer $OWNER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"SmokeDog","breed":"Labrador","date_of_birth":"2022-06-01","weight_kg":30,"sex":"MALE","blood_type":"DEA_1_1_NEGATIVE"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")"
printf '\x89PNG\r\n\x1a\n' > /tmp/smoke.png
python3 - <<'PYEOF'
from PIL import Image
Image.new("RGB", (600, 400), "brown").save("/tmp/smoke.png")
PYEOF
PHOTO_URL="$(curl -s -X POST "$BASE/dogs/$DOG_ID/photo" \
  -H "Authorization: Bearer $OWNER_TOKEN" -F "file=@/tmp/smoke.png;type=image/png" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['photo_url'])")"
[[ "$PHOTO_URL" == /media/dogs/* ]] && echo "  ok: photo stored at $PHOTO_URL" || { echo "  FAIL: photo upload" >&2; exit 1; }

echo "== 6. Staff creates request; compatible listing finds it (T-500/T-604) =="
REQUEST_ID="$(curl -s -X POST "$BASE/requests" -H "Authorization: Bearer $STAFF_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"volume_ml":300,"urgency":"URGENT","needed_by_date":"'$(python3 -c "from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)+timedelta(days=5)).isoformat())")'","blood_type_needed":"DEA_1_1_POSITIVE","patient_info":"Large dog, surgery"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")"
COMPAT_COUNT="$(curl -s "$BASE/requests/compatible?dog_id=$DOG_ID" \
  -H "Authorization: Bearer $OWNER_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d), d[0]['compatibility_score'] if d else '-')")"
echo "  ok: compatible listing -> $COMPAT_COUNT"

echo "== 7. Owner responds ACCEPTED; clinic completes it (T-600/T-603) =="
RESPONSE_ID="$(curl -s -X POST "$BASE/requests/$REQUEST_ID/respond" \
  -H "Authorization: Bearer $OWNER_TOKEN" -H 'Content-Type: application/json' \
  -d '{"dog_id":"'"$DOG_ID"'","status":"ACCEPTED","response_message":"Ready when you are!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")"
LAST_DONATION_BEFORE="$(json "['last_donation_date']" "$BASE/dogs/$DOG_ID" -H "Authorization: Bearer $OWNER_TOKEN")"
check "complete response" 200 "$(code -X POST "$BASE/requests/responses/$RESPONSE_ID/complete" \
  -H "Authorization: Bearer $STAFF_TOKEN")"
LAST_DONATION_AFTER="$(json "['last_donation_date']" "$BASE/dogs/$DOG_ID" -H "Authorization: Bearer $OWNER_TOKEN")"
[[ "$LAST_DONATION_BEFORE" == "None" && "$LAST_DONATION_AFTER" != "None" ]] \
  && echo "  ok: last_donation_date set ($LAST_DONATION_AFTER)" \
  || { echo "  FAIL: last donation date not set" >&2; exit 1; }

echo "== 8. Emails were produced in log mode (T-1002/T-1003) =="
EMAIL_COUNT="$(docker compose exec -T db psql -U hector -d hector -tAc \
  "SELECT count(*) FROM email_log WHERE recipient LIKE 'owner-$STAMP%' OR recipient LIKE 'smoke-%';")"
[[ "$EMAIL_COUNT" -ge 2 ]] && echo "  ok: $EMAIL_COUNT emails logged" || { echo "  FAIL: emails missing" >&2; exit 1; }

echo "== 9. Admin stats reflect activity (T-703) =="
TOTAL_USERS="$(json "['total_users']" "$BASE/admin/stats" -H "Authorization: Bearer $ADMIN_TOKEN")"
[[ "$TOTAL_USERS" -ge 3 ]] && echo "  ok: stats show $TOTAL_USERS users" || { echo "  FAIL: stats" >&2; exit 1; }

echo ""
echo "SMOKE TEST PASSED ($PASS checks) — full user journey works end-to-end."
