from pydantic import RootModel

from src.pydb.configtypes import Config


class ConfigModels(RootModel):
    root: dict[str, Config]


CONFIGS = ConfigModels.model_validate_json(
    open("tests/env/connection.json").read()
)

TEST_TABLES = {
    "mysql": [
        "drop table if exists users",
        """
            CREATE TABLE `users` (
            `id` int NOT NULL,
            `name` varchar(100) NOT NULL,
            `email` varchar(100) NOT NULL,
            `amount` decimal(12,2) NOT NULL,
            PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
    ],
    "psql": [
        "DROP TABLE IF EXISTS users",
        """
            CREATE TABLE IF NOT EXISTS users
            (
                id integer NOT NULL,
                name character varying(100) COLLATE pg_catalog."default" NOT NULL,
                email character varying(100) COLLATE pg_catalog."default" NOT NULL,
                amount numeric(20,4) NOT NULL,
                CONSTRAINT users_pkey PRIMARY KEY (id)
            )
        """,
    ],
}

TABLE_METADATA = {
    "psql": [
        "drop table if exists test_metadata",
        """
                CREATE TABLE public.test_metadata
                (
                    id integer NOT NULL,
                    name character varying(30) NOT NULL DEFAULT 'name',
                    value_float numeric(10, 2),
                    value_json jsonb,
                    "camelCase" integer,
                    PRIMARY KEY (id, name)
                )
                """,
    ],
    "mysql": [
        "drop table if exists test_metadata",
        """
                CREATE TABLE test_metadata
                (
                    id int NOT NULL,
                    name varchar(30) NOT NULL DEFAULT 'name',
                    value_float decimal(10, 2),
                    value_json text,
                    camelCase int,
                    PRIMARY KEY (id, name)
                )    
                """,
    ],
}
