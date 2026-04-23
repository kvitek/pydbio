#!/usr/bin/env bash

DATABASE=$1
USER=$2
PASSWORD="$(openssl rand -base64 10)"

cat > sample.sql <<EOF
\connect postgres

\restrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp
DROP DATABASE IF EXISTS "$DATABASE" WITH (FORCE);
DROP OWNED BY "$USER";
DROP USER "$USER";
CREATE DATABASE "${DATABASE}";
CREATE USER "$USER" WITH PASSWORD '${PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE "$DATABASE" TO "$USER";
\unrestrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp

\connect "$DATABASE"

\restrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp
GRANT ALL PRIVILEGES ON SCHEMA public TO "$USER";
\unrestrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp
EOF

echo "Database: ${DATABASE}"
echo "User: ${USER}"
echo "Password: ${PASSWORD}"

cp prepare_psql.sql /mnt/e/db/postgres18/workdir
docker exec -it mgdev-18 bash