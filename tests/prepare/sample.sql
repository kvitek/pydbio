\connect postgres

\restrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp
DROP DATABASE IF EXISTS "up_test" WITH (FORCE);
DROP OWNED BY "up_test_user";
DROP USER "up_test_user";
CREATE DATABASE "up_test";
CREATE USER "up_test_user" WITH PASSWORD 'bpxDQ/FSYY9u3Q==';
GRANT ALL PRIVILEGES ON DATABASE "up_test" TO "up_test_user";
\unrestrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp

\connect "up_test"

\restrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp
GRANT ALL PRIVILEGES ON SCHEMA public TO "up_test_user";
\unrestrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp
