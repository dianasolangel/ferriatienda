# ────────────────
# Makefile for FerrIAtienda RAG Project ONLY DEV IMPLEMENTATION FOR NOW
# ────────────────

APP_NAME=ferriatienda_app

# We build the Docker image
build:
	docker compose build

#We start the containers in detached mode
up:
	docker compose up -d

# We rebuild the vector database if needed
rebuild-db:
	docker compose run --rm ferriatienda_app poetry run python ferriatienda/embedding/build_vectorstore.py

# Show container logs
logs:
	docker compose logs -f $(APP_NAME)

# Run the app interactively (no daemon mode)
run:
	docker compose run --rm --service-ports $(APP_NAME)

# Rebuild everything from scratch
reset:
	docker compose down --volumes --remove-orphans
	docker compose build --no-cache
	make up
# To test the docker setup locally
test:
	./test_docker_local.sh