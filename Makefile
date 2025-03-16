ifeq (,$(wildcard .env))
$(error .env file is missing. Please create one based on .env.example)
endif

include .env

# --- Infrastructure ---
local-docker-infrastructure-up:
	docker compose up -d
local-docker-infrastructure-down:
	docker compose stop

local-zenml-server-up:
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES poetry run zenml login --local

local-zenml-server-stop:
	poetry run zenml logout --local

local-infrastructure-up: local-docker-infrastructure-up local-zenml-server-stop local-zenml-server-up

local-infrastructure-down: local-docker-infrastructure-down local-zenml-server-stop


# --- Offline ML Pipelines ---
feature-pipeline:
	poetry run python -m src.tools.run --run-feature-pipeline --no-cache


# --- Docker ---
build-docker-image:
	docker buildx build --platform linux/amd64 -t rag_llmops -f Dockerfile .
run-docker-feature-pipeline:
	docker run --rm --network host rag_llmops make feature-pipeline