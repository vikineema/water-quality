#!make
SHELL := /usr/bin/env bash

setup: up install-python-pkgs init get-jupyter-token

build:
	docker compose build 

## Environment setup
up: ## Bring up your Docker environment
	docker compose up -d postgres
	docker compose run checkdb
	docker compose up -d jupyter
	docker compose up -d geoserver
	docker compose up -d pgadmin4
	make init
	make add-products
	make install-python-pkgs

reset: ## Stop all services, delete volumes, recreate volumes then restart all the servces 
	make  down

init: ## Prepare the database
	docker compose exec -T jupyter datacube -v system init

down: ## Bring down your Docker environment
	docker compose down --remove-orphans

logs: ## View logs for all services
	docker compose logs 

install-python-pkgs:
	docker compose exec jupyter bash -c "cd /home/jovyan && pip install -e ."

lint-src:
	ruff check --select I --fix src/
	ruff format --verbose src/

add-products:
	docker compose exec -T jupyter dc-sync-products products/products.csv

## Jupyter service
start-jupyter: ## To be used in micromamba-shell
	cp docker/assets/jupyter_lab_config.py ${CONDA_PREFIX}/etc/jupyter/jupyter_lab_config.py
	nohup jupyter lab > /dev/null 2>&1 &
	sleep 10s
	jupyter lab list

get-jupyter-token: ## View the secret token for jupyterlab
	## Also available in .local/share/jupyter/runtime/jupyter_cookie_secret
	docker compose exec -T jupyter jupyter lab list

jupyter-shell: ## Open shell in jupyter service
	docker compose exec jupyter /bin/bash

## Postgres service
db-shell:
	PGPASSWORD=opendatacubepassword \
	pgcli -h localhost -p 5434 -U opendatacube -d postgres

## Explorer
setup-explorer: ## Setup the datacube explorer
	# Initialise and create product summaries
	docker compose up -d explorer
	docker compose exec -T explorer cubedash-gen --init --all
	# Services available on http://localhost:8080/products

explorer-refresh-products:
	docker compose exec -T explorer cubedash-gen --init --all

# index-wofs-all-time-summary
index-wofs_ls_summary_alltime:
	@echo "$$(date) Start with wofs_ls_summary_alltime"
	docker compose exec -T jupyter stac-to-dc \
		--catalog-href=https://explorer.digitalearth.africa/stac/ \
		--collections=wofs_ls_summary_alltime 
	@echo "$$(date) Done with wofs_ls_summary_alltime"


# Generate stac files
create-stac-files:
	mprof run cgls-lwq  create-stac-files \
	--product-name=cgls_lwq300_2002_2012 \
	--product-yaml=products/cgls_lwq300_2002_2012.odc-product.yaml \
	--stac-output-dir=data/cgls_lwq300_2002_2012 \
	--no-overwrite \
	--write-eo3 \
	-vvv

download-cog-files:
	mprof run cgls-lwq  download-cogs \
	--product-name=cgls_lwq300_2002_2012 \
	--cog-output-dir=data/cgls_lwq300_2002_2012/new_tiling \
	--no-overwrite \
	-vvv

upload-to-s3:
	find data/cgls_lwq300_2002_2012/*/*/2011/01 -type f | while read -r file; do \
		relpath=$$(echo "$$file" | sed 's|^data/||'); \
		aws s3 cp --dry-run "$$file" "s3://$(S3_BUCKET)/$$relpath"; \
	done	
