#!make
SHELL := /usr/bin/env bash

setup: up init get-jupyter-token

## Environment setup
up: ## Bring up your Docker environment
	docker compose up -d postgres
	docker compose run checkdb
	docker compose up -d jupyter
	docker compose up -d geoserver
	docker compose up -d pgadmin4

reset: ## Stop all services, delete volumes, recreate volumes then restart all the servces 
	make  down

init: ## Prepare the database
	docker compose exec -T jupyter datacube -v system init

down: ## Bring down your Docker environment
	docker compose down --remove-orphans

logs: ## View logs for all services
	docker compose logs 

get-jupyter-token: ## View the secret token for jupyterlab
	## Also available in .local/share/jupyter/runtime/jupyter_cookie_secret
	docker compose exec -T jupyter jupyter notebook list

shell: ## Open shell in jupyter service
	docker compose exec jupyter bash -c "cd /home/jovyan/ && exec bash"

## Explorer
setup-explorer: ## Setup the datacube explorer
	# Initialise and create product summaries
	docker compose up -d explorer
	docker compose exec -T explorer cubedash-gen --init --all
	# Services available on http://localhost:8080/products

explorer-refresh-products:
	docker compose exec -T explorer cubedash-gen --init --all