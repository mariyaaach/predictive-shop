#!/bin/bash
set -e

# Вывод всех переменных окружения для отладки
env

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE name_bd;
EOSQL