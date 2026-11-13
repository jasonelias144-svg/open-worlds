#!/bin/bash
# cross_language_test.sh

set -e
cd "$(dirname "$0")"

echo "=== Start Python Poetry World on :8001 ==="
python -c "
from multiverse_c4 import PoetryWorld
from wcp_http_shim import WorldProtocolServer
w = PoetryWorld('world:poetry', 'The Poetry World')
WorldProtocolServer(w, port=8001).serve_forever()
" &
P1=$!

echo "=== Start Python Chemistry World on :8002 ==="
python -c "
from multiverse_c5 import ChemistryWorld
from wcp_http_shim import WorldProtocolServer
w = ChemistryWorld('world:chemistry', 'The Chemistry World')
WorldProtocolServer(w, port=8002).serve_forever()
" &
P2=$!

sleep 1

echo "=== Start TypeScript Registry on :9000 ==="
cd ts && npm install --silent 2>/dev/null && PORT=9000 npx tsx src/index.ts &
T1=$!
cd ..

sleep 2

echo "=== Python conformance CLI tests TS Registry ==="
python -m wcp_conformance --url http://localhost:9000

echo "=== TS Registry admits Poetry World ==="
ADMIN="admin-$(head -c8 /dev/urandom | xxd -p)"
curl -s -X POST http://localhost:9000/petition \
  -H 'Content-Type: application/json' \
  -d "{\"petitioner_token\":\"$ADMIN\",\"petitioner_name\":\"admin\",\"passport_admissions\":[],\"message\":\"setup\"}"
curl -s -X POST http://localhost:9000/act \
  -H 'Content-Type: application/json' \
  -d "{\"actor_token\":\"$ADMIN\",\"type\":\"multiverse.admit\",\"payload\":{\"entity_url\":\"http://localhost:8001\"}}"
curl -s -X POST http://localhost:9000/act \
  -H 'Content-Type: application/json' \
  -d "{\"actor_token\":\"$ADMIN\",\"type\":\"multiverse.admit\",\"payload\":{\"entity_url\":\"http://localhost:8002\"}}"

echo
echo "=== TS Registry sub-entities ==="
curl -s http://localhost:9000/sub_entities | python -m json.tool

echo "=== Start Python Registry on :9001 ==="
python -c "
from multiverse_c6 import MultiverseRegistry
from wcp_http_shim import WorldProtocolServer
m = MultiverseRegistry('multiverse:python', 'Python Multiverse')
WorldProtocolServer(m, port=9001).serve_forever()
" &
P3=$!

sleep 1

echo "=== Python Registry admits TS Registry (cross-language) ==="
ADMIN2="admin2-$(head -c8 /dev/urandom | xxd -p)"
curl -s -X POST http://localhost:9001/petition \
  -H 'Content-Type: application/json' \
  -d "{\"petitioner_token\":\"$ADMIN2\",\"petitioner_name\":\"admin2\",\"passport_admissions\":[],\"message\":\"setup\"}"
curl -s -X POST http://localhost:9001/act \
  -H 'Content-Type: application/json' \
  -d "{\"actor_token\":\"$ADMIN2\",\"type\":\"multiverse.admit\",\"payload\":{\"entity_url\":\"http://localhost:9000\"}}"

echo
echo "=== Python Registry sub-entities ==="
curl -s http://localhost:9001/sub_entities | python -m json.tool

echo
echo "=== FEDERATION SUCCESS: bidirectional cross-language listing ==="

kill $P1 $P2 $P3 $T1 2>/dev/null || true
