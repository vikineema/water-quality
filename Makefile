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
	docker compose exec -T jupyter dc-sync-products products/products.csv --update-if-exists

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

## cgls_lwq300_2002_2012
download-cog-files-cgls_lwq300_2002_2012:
	mprof run cgls-lwq  download-cogs \
	--product-name=cgls_lwq300_2002_2012 \
	--cog-output-dir=s3://deafrica-water-quality-dev/cgls_lwq300_2002_2012/ \
	--no-overwrite \
	-vvv

create-stac-files-cgls_lwq300_2002_2012: ## Create per dataset metadata for a LWQ product
	mprof run cgls-lwq  create-stac-files \
	--cogs-dir=s3://deafrica-water-quality-dev/cgls_lwq300_2002_2012/ \
	--product-yaml=products/cgls_lwq300_2002_2012.odc-product.yaml \
	--stac-output-dir=s3://deafrica-water-quality-dev/cgls_lwq300_2002_2012/ \
	--no-overwrite \
	--no-write-eo3 \
	-vvv

index-stac-cgls_lwq300_2002_2012:
	docker compose exec -T jupyter s3-to-dc-v2 \
	--stac --no-sign-request --update-if-exists --allow-unsafe \
	s3://deafrica-water-quality-dev/cgls_lwq300_2002_2012/**/*.json \
	cgls_lwq300_2002_2012


## cgls_lwq300_2016_2024
download-cog-files-cgls_lwq300_2016_2024:
	docker compose exec -T jupyter \
		mprof run cgls-lwq  download-cogs \
		--product-name=cgls_lwq300_2016_2024 \
		--cog-output-dir=data/cgls_lwq300_2016_2024/ \
		--url-filter="201605" \
		--no-overwrite \
		-vvv

copy-cogs-to-s3-cgls_lwq300_2016_2024:
	aws s3 cp --recursive --no-sign-request \
	data/cgls_lwq300_2016_2024/ \
	s3://deafrica-water-quality-dev/cgls_lwq300_2016_2024/ 

create-stac-files-cgls_lwq300_2016_2024: ## Create per dataset metadata for a LWQ product
	mprof run cgls-lwq  create-stac-files \
	--cogs-dir=s3://deafrica-water-quality-dev/cgls_lwq300_2016_2024/ \
	--product-yaml=products/cgls_lwq300_2016_2024.odc-product.yaml \
	--stac-output-dir=s3://deafrica-water-quality-dev/cgls_lwq300_2016_2024/ \
	--no-overwrite \
	--no-write-eo3 \
	-vvv

index-stac-cgls_lwq300_2016_2024:
	docker compose exec -T jupyter s3-to-dc-v2 \
	--stac --no-sign-request --update-if-exists --allow-unsafe \
	s3://deafrica-water-quality-dev/cgls_lwq300_2016_2024/**/*.json \
	cgls_lwq300_2016_2024


## cgls_lwq100_2019_2024
download-cog-files-cgls_lwq100_2019_2024:
	## docker compose exec -T jupyter \
	mprof run cgls-lwq  download-cogs \
	--product-name=cgls_lwq100_2019_2024 \
	--cog-output-dir=data/cgls_lwq100_2019_2024/ \
	--url-filter="202403" \
	--no-overwrite \
	-vvv


## cgls_lwq300_2024_nrt
download-cog-files-cgls_lwq300_2024_nrt:
	## docker compose exec -T jupyter \
	mprof run cgls-lwq  download-cogs \
	--product-name=cgls_lwq300_2024_nrt \
	--cog-output-dir=data/cgls_lwq300_2024_nrt/ \
	--url-filter="202503" \
	--no-overwrite \
	-vvv


## cgls_lwq100_2024_nrt
download-cog-files-cgls_lwq100_2024_nrt:
	## docker compose exec -T jupyter \
	mprof run cgls-lwq  download-cogs \
	--product-name=cgls_lwq100_2024_nrt \
	--cog-output-dir=data/cgls_lwq100_2024_nrt/ \
	--url-filter="202503" \
	--no-overwrite \
	-vvv