#!/bin/bash
set -e
if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
  IFS=',' read -ra DBS <<< "$POSTGRES_MULTIPLE_DATABASES"
  for db in "${DBS[@]}"; do
    if [ "$db" != "$POSTGRES_DB" ]; then
      echo "Creating database '$db'"
      psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $db;
        GRANT ALL PRIVILEGES ON DATABASE $db TO $POSTGRES_USER;
EOSQL
    fi
  done
fi
