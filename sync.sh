#!/bin/bash

# args:
# 1 dataset name
#
# example:
#   bash ../../scripts/sync.sh de_bundestag_dip

aws s3 --endpoint-url https://minio.ninja cp --no-progress s3://catalog.investigativedata.org/$1/datastore.sqlite3 data/datastore.sqlite3
