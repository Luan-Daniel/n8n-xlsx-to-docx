#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="n8n-custom"
IMAGE_NAME="n8n-custom:local"
ENV_FILE="$SCRIPT_DIR/.env"
HOST_DATA_DIR="$SCRIPT_DIR/n8n-data"
DB="$HOST_DATA_DIR/database.sqlite"
SETUP_FLAG="/home/node/.n8n_setup_done"

set -a
source "$ENV_FILE"
set +a

until [[ "$(curl -s -o /dev/null -w "%{http_code}" "$N8N_URL")" =~ ^2 ]]; do
  echo "  [i] Waiting for N8N to be ready..."
  sleep 5
done

if docker exec "$CONTAINER_NAME" sh -c "[ -f \"$SETUP_FLAG\" ]"; then
  echo -e "  [i] Setup already completed. Skipping \033[2;90m[trigger:setup_complete]\033[0m"
  exit 0
fi

until [[ -f "$DB" ]]; do
  echo "  [i] Waiting for n8n database to be created..."
  sleep 3
done

if ! command -v sqlite3 &> /dev/null; then
  echo -e "  \033[41m\033[37m[!]\033[0m sqlite3 is not installed. Please install it to proceed with the n8n setup."
  exit 1
fi
if ! command -v jq &> /dev/null; then
  echo -e "  \033[41m\033[37m[!]\033[0m jq is not installed. Please install it to proceed with the n8n setup."
  exit 1
fi


# -- Helper functions --

extract_workflow_id() {
  local json="$1"
  echo "$json" | jq -r '.id'
}

# -- N8N SETUP START --

# Check if npm packages are installed (for community nodes)
if ! docker exec -it -u root "$CONTAINER_NAME" sh -c "ls /home/node/.n8n/nodes/node_modules/" >/dev/null 2>&1; then
  echo "  [i] npm packages not found. Installing..."
  # Install the JS charting library and statistical libraries (not sure if this will work inside the n8n script nodes)
  docker exec -it -u root "$CONTAINER_NAME" sh -c "npm install -g chartjs-node-canvas@4 simple-statistics jstat mathjs @stdlib/stats-kruskal-test --save"
  # Install docxtemplater node
  docker exec -it -u root "$CONTAINER_NAME" sh -c "cd /home/node/.n8n/nodes && npm install n8n-nodes-docxtemplater@1.0.1 --save"
else
  echo "  [i] Node modules directory found. Will assume packages are installed. (did not check individual packages)"
fi

# User setup
sleep 5 # give the db some time to get ready (the alternative is checking. maybe a thing todo later)
IS_SETUP_DONE=$(sqlite3 "$DB" "SELECT value FROM settings WHERE key = 'userManagement.isInstanceOwnerSetUp';")
if [[ "$IS_SETUP_DONE" == "true" ]]; then
  echo -e "  [i] n8n instance owner already set up.\n"\
          "     Script will expect the owner API key to be created and set in the environment variable \033[1;33mN8N_USER_API_KEY\033[0m."
else
  echo "  [i] Setting up n8n user and API key from environment variables"
  OWNER_ID=$(sqlite3 "$DB" "SELECT id FROM user WHERE role = 'global:owner' LIMIT 1;")
  sqlite3 "$DB" <<EOF
UPDATE user SET
  email = '${N8N_USER_EMAIL}',
  password = '${N8N_USER_PASSWORD_HASH}',
  firstName = '${N8N_USER_FIRST_NAME}',
  lastName = '${N8N_USER_LAST_NAME}',
  settings = '{"userActivated":true}'
WHERE id = '${OWNER_ID}';
EOF
  sqlite3 "$DB" <<EOF
UPDATE settings SET
  value = 'true'
WHERE key = 'userManagement.isInstanceOwnerSetUp';
EOF
  API_KEY_ID=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)
  sqlite3 "$DB" <<EOF
INSERT INTO user_api_keys (id, label, userId, apiKey, createdAt, updatedAt, scopes)
VALUES ('${API_KEY_ID}', 'owner-eternal-api-key', '${OWNER_ID}', '${N8N_USER_API_KEY}', datetime('now'), datetime('now'), '${N8N_USER_API_KEY_SCOPES}');
EOF
  docker restart "$CONTAINER_NAME" > /dev/null
  echo "  [i] Restarted n8n to apply changes"
fi

until [[ "$(curl -s -o /dev/null -w "%{http_code}" "$N8N_URL")" =~ ^2 ]]; do
  echo "  [i] Waiting for N8N to be ready..."
  sleep 5
done

# Workflow setup (yet to be finished) (its a mess right now)

if false; then # skip for now
  resp=$(curl -sS -X POST "$N8N_URL/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_USER_API_KEY" \
    -H "Content-Type: application/json" \
    -H "accept: application/json" \
    -d "{
      \"name\": \"Webhook to File\",
      \"nodes\": [
        {
          \"parameters\": {
            \"path\": \"$SETUP_WEBHOOK_PATH\",
            \"http_method\": \"POST\"
          },
          \"name\": \"Webhook\",
          \"type\": \"n8n-nodes-base.webhook\",
          \"typeVersion\": 1,
          \"position\": [240, 300],
          
        },
        {
          \"parameters\": {
            \"file_name\": \"/tmp/test-output.txt\", # not working for some reason, it asks for fileName
            \"data\": \"={{JSON.stringify(\$json)}}\"
          },
          \"name\": \"Write File\",
          \"type\": \"n8n-nodes-base.writeBinaryFile\",
          \"typeVersion\": 1,
          \"position\": [480, 300]
        }
      ],
      \"connections\": {
        \"Webhook\": {
          \"main\": [
            [
              {
                \"node\": \"Write File\",
                \"type\": \"main\",
                \"index\": 0
              }
            ]
          ]
        }
      },
      \"settings\": {}
    }"
  )
  echo "  [debug] Workflow creation response: $resp"
  workflow_id=$(extract_workflow_id "$resp")
  echo "  [debug] Workflow ID: $workflow_id"
  curl -sS -X POST "$N8N_URL/api/v1/workflows/$workflow_id/activate" \
    -H "X-N8N-API-KEY: $N8N_USER_API_KEY" \
    -H "Content-Type: application/json" \
    -H "accept: application/json" > /dev/null
fi

# -- N8N SETUP END --
docker exec "$CONTAINER_NAME" sh -c "touch \"$SETUP_FLAG\""
echo -e "  [i] N8N setup complete. \033[2;90m[trigger:setup_complete]\033[0m"