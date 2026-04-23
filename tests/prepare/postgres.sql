\ connect postgres \ restrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp DROP DATABASE IF EXISTS test WITH (FORCE);
DROP OWNED BY test_user;
DROP USER test_user;
CREATE DATABASE test;
CREATE USER test_user WITH PASSWORD '';
GRANT ALL PRIVILEGES ON DATABASE test TO test_user;
\ unrestrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp \ connect test \ restrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp DROP TABLE IF EXISTS public.users;
GRANT ALL PRIVILEGES ON SCHEMA public TO test_user;
CREATE TABLE IF NOT EXISTS public.users (
    id integer NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    email character varying(100) COLLATE pg_catalog."default" NOT NULL,
    amount numeric(20, 4) NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;
ALTER TABLE IF EXISTS public.users OWNER to test_user;
\ unrestrict KRvdiWPbtVUKfQzJGC3uMKulxMfgZpn5pzEg641en3llVwbZHEV7ZyUiYnucGNp