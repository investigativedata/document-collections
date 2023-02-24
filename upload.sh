#!/bin/bash

# args:
# 1 dataset name

# documents (do first bc if that fails, we should not update metadata)
aws s3 --endpoint-url https://minio.ninja sync --no-progress data/store/$1 s3://catalog.investigativedata.org/$1/documents
# entities
aws s3 --endpoint-url https://minio.ninja cp --no-progress data/export/entities.ftm.json s3://catalog.investigativedata.org/$1/entities/`date +"%Y-%m-%d_%H_%M_%S"`.ftm.json
# memorious db
aws s3 --endpoint-url https://minio.ninja cp --no-progress data/datastore.sqlite3 s3://catalog.investigativedata.org/$1/
# index
aws s3 --endpoint-url https://minio.ninja cp --no-progress data/export/index.json s3://catalog.investigativedata.org/$1/
