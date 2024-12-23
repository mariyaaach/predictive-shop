#!/bin/bash
set -e


psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" <<-EOSQL
    CREATE DATABASE users_service;
    CREATE DATABASE orders_service;
    CREATE DATABASE products_service;
EOSQL