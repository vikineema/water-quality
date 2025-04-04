#!make
SHELL := /usr/bin/env bash

setup: up init get-jupyter-token

build:
	docker compose build 

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

## Jupyter service
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

## Download required datasets
download-waterbodies-gpkg:
	mkdir -p data
	ogr2ogr -f Parquet data/waterbodies.parquet \
	"/vsicurl/https://deafrica-services.s3.af-south-1.amazonaws.com/waterbodies/v0.0.3/historical_extent/waterbodies.gpkg"

download-glrglsed: ## Download the GLRSED dataset split by continent
	mkdir -p data
	# Download file
	curl -L "https://zenodo.org/records/14190225/files/GLRSED_shp_V1.2_by%20continent.zip?download=1" \
	-o "data/GLRSED_shp_V1.2_by continent.zip"
	# Unzip downloaded file
	unzip "data/GLRSED_shp_V1.2_by continent.zip" -d data/
	# Delete downloaded zip file
	rm "data/GLRSED_shp_V1.2_by continent.zip"
	# Delete data not for Africa
	find "data/GLRSED_shp_V1.2_by continent/" -type f ! -name "*AF*" -exec rm  {} +

download-hydroatlas-lakeatlas: ## Download HydroATLAS LakeATLAS
	mkdir -p data
	# Download zip file 
	curl -L https://figshare.com/ndownloader/files/35959547 \
		-o data/LakeATLAS_Data_v10_shp.zip
	# Unzip downloaded file
	unzip data/LakeATLAS_Data_v10_shp.zip -d data/
	# Delete downloaded zip file
	rm data/LakeATLAS_Data_v10_shp.zip
	
download-realsate: ## Download the ReaLSAT reference shape of waterbodies
	mkdir -p data
	# Download zip file
	curl -L https://zenodo.org/records/7614815/files/ReaLSAT-2-0.zip \
	-o data/ReaLSAT-2-0.zip 
	# Unzip downloaded file
	unzip data/ReaLSAT-2-0.zip -d data/
	# Delete zip file
	rm data/ReaLSAT-2-0.zip
