set -e

echo "Cleaning old containers and volumes..."
docker compose down --volumes --remove-orphans

echo "Building fresh Docker image..."
docker compose build --no-cache

echo "Starting app in background..."
docker compose up -d

echo "Waiting 10 seconds for services to boot..."
sleep 10

echo "Checking if Chroma vectorstore was created..."
docker exec ferriatienda_app bash -c 'test "$(ls -A /app/chroma)" && echo "Vectorstore exists and is populated." || echo "⚠️ Vectorstore is empty or missing!"'

echo "App is running at: http://localhost:8501"

#TO TEST LOCALLY:
# chmod +x test_docker_local.sh
# ./test_docker_local.sh