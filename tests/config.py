from pydbio.basicio import configure
from pydbio.configtypes import Config, Dialects

CONFIGS = {
    # "psql": Config(
    #     host="127.0.0.1",
    #     port=6543,
    #     user="mgp_prod",
    #     password="58fGWd74",
    #     database="mgp_prod_replical",
    #     dialect=Dialects("psql"),
    # ),
    "psql": Config(
        host="127.0.0.1",
        port=6543,
        user="test_user",
        password="dDt5RgxCV7fxLA",
        database="test",
        dialect=Dialects("psql"),
    ),
    # "mysql": Config(
    #     host="127.0.0.1",
    #     port=3306,
    #     user="app",
    #     password="Burkina!7faso",
    #     database="test_",
    #     dialect=Dialects("mysql"),
    #     ssl_ca="/mnt/mysql/ca.pem",
    #     ssl_cert="/mnt/mysql/client-cert.pem",
    #     ssl_key="/mnt/mysql/client-key.pem",
    # ),
    "mysql": Config(
        host="127.0.0.1",
        port=3307,
        user="admin",
        password="Burkina@6faso",
        database="reports",
        dialect=Dialects("mysql"),
        # ssl_ca="/mnt/mysql/ca.pem",
        # ssl_cert="/mnt/mysql/client-cert.pem",
        # ssl_key="/mnt/mysql/client-key.pem",
    ),
}

configure(CONFIGS)

TABLE_METADATA = {
    "psql": [
        "drop table if exists test_metadata",
        """
                CREATE TABLE public.test_metadata
                (
                    id integer NOT NULL,
                    name character varying(30) NOT NULL,
                    value_float numeric(10, 2),
                    value_json jsonb,
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
                    name varchar(30) NOT NULL,
                    value_float decimal(10, 2),
                    value_json text,
                    PRIMARY KEY (id, name)
                )    
                """,
    ],
}
