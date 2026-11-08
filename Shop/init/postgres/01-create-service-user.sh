#!/bin/bash
set -euo pipefail

# Runs only on first initialization of the shop PostgreSQL volume.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v service_password="$SHOP_SERVICE_PASSWORD" <<'EOSQL'

SELECT format('CREATE ROLE shop_service WITH LOGIN PASSWORD %L', :'service_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shop_service')
\gexec

GRANT CONNECT ON DATABASE shop_db TO shop_service;
GRANT USAGE, CREATE ON SCHEMA public TO shop_service;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO shop_service;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO shop_service;
ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO shop_service;
ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO shop_service;
EOSQL
