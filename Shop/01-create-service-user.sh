#!/bin/bash
set -euo pipefail

# This script runs only when PostgreSQL initializes an EMPTY data directory.
# Existing service passwords are reused; no password values are changed.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v service_password="$SHOP_SERVICE_PASSWORD" <<'EOSQL'

-- Create the shop role if it does not already exist.
SELECT format('CREATE ROLE shop_service WITH LOGIN PASSWORD %L', :'service_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shop_service')
\gexec

-- Create the auth role with the existing service password if absent.
SELECT format('CREATE ROLE auth_service WITH LOGIN PASSWORD %L', :'service_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_service')
\gexec

-- POSTGRES_DB is shop_db, so it already exists at initialization.
GRANT CONNECT ON DATABASE shop_db TO shop_service;
GRANT USAGE, CREATE ON SCHEMA public TO shop_service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO shop_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO shop_service;
ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO shop_service;
ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO shop_service;

-- CREATE DATABASE cannot run inside a transaction; psql's \gexec executes it separately.
SELECT 'CREATE DATABASE auth_db OWNER auth_service'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'auth_db')
\gexec

GRANT CONNECT ON DATABASE auth_db TO auth_service;
EOSQL

# Grant schema permissions inside auth_db so SQLAlchemy can create users table.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname auth_db <<'EOSQL'
GRANT USAGE, CREATE ON SCHEMA public TO auth_service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auth_service;
EOSQL
