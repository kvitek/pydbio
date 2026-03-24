import inspect
import random
import time
import unittest
from decimal import Decimal
from typing import Any, Tuple, cast

from pydb.configtypes import Config
from src.pydb.basicio import configure, configure_close, get_connection
from src.pydb.pgio import PSQL, ConnectionPool, PSQLConnection
from tests.config import CONFIGS, TEST_TABLES


def gen_data_set(length: int) -> list[Tuple[int, str, str, Decimal]]:
    return [
        (
            i + 1,
            f"name {i}",
            f"name{i}@example.com",
            Decimal(random.randrange(0, 10000)) / 10,
        )
        for i in range(length)
    ]


def format_time(seconds: float) -> str:
    """
    Format seconds to HH:MM:SS:ms format.

    Args:
        seconds: Number of seconds

    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msec = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{msec:03d}"


POOL: ConnectionPool | None = None


def config_to_conninfo(config: Config) -> str:

    return f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"


def open_connection_pool():
    global POOL
    if POOL is not None:
        return

    conninfo = config_to_conninfo(CONFIGS.root["psql"])

    POOL = ConnectionPool(conninfo=conninfo, min_size=4, max_size=10, open=True)


class TestPerformancePSQL(unittest.TestCase):
    data: list[Any] = []
    results: dict[str, str] = {}

    @classmethod
    def setUpClass(cls) -> None:
        configure(CONFIGS.root)

        cls.data = gen_data_set(1000000)
        cls.results = {}

    def setUp(self):
        con = get_connection("psql")
        con.execute("truncate table users")
        con.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        configure_close()
        for name, r in cls.results.items():
            print(name, r)

    def test_one_chunk(self):
        query = """
            insert into users (id, name, email, amount) 
            values (%s, %s, %s, %s)"""

        con = get_connection("psql")

        st = time.time()
        con.executemany(query=query, data=self.data)
        con.commit()
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_chunks_with_commit(self):
        CHUNK_SIZE = 10000
        query = """
            insert into users (id, name, email, amount) 
            values (%s, %s, %s, %s)"""

        con = get_connection("psql")

        chunks = int(len(self.data) / CHUNK_SIZE)
        st = time.time()
        for i in range(chunks):
            con.executemany(
                query=query,
                data=self.data[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE],
            )
        con.commit()
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_copy_from(self):
        con = cast(PSQL, get_connection("psql"))

        st = time.time()
        con.copy_from(
            self.data,
            columns=("id", "name", "email", "amount"),
            table_name="users",
        )
        con.commit()
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_big_query(self):
        con = get_connection("psql")

        st = time.time()
        buffer = 'insert into public.users ("id", name, email, amount) values '
        buffer += ",".join(
            (
                f"({row[0]},'{row[1]}','{row[2]}','{row[3]}')"
                for row in self.data
            )
        )
        con.execute(buffer)
        con.commit()
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_connection_pool(self):
        ITERATIONS = 1000
        open_connection_pool()

        st = time.time()
        for i in range(ITERATIONS):
            if POOL is None:
                raise RuntimeError()

            with POOL.connection() as con:
                with con.cursor() as cur:
                    cur.execute("select 1+1")
                    cur.fetchall()

        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_connection(self):
        ITERATIONS = 1000
        con = get_connection("psql")

        st = time.time()
        for i in range(ITERATIONS):
            con.fetch_tuples("select 1+1")
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_reconnect(self):
        conn = get_connection("psql")

        with self.subTest("close"):
            conn.close()
            conn.fetch_tuples("select 1+1")

        with self.subTest("unfetched results"):
            conn.execute("select 1+1")
            conn.fetch_tuples("select 1+1")


class TestPerformanceMySQL(unittest.TestCase):
    data: list[Any] = []
    results: dict[str, str] = {}

    @classmethod
    def setUpClass(cls) -> None:
        configure(CONFIGS.root)

        cls.data = gen_data_set(1000000)
        cls.results = {}

        con = get_connection("mysql")
        for query in TEST_TABLES["mysql"]:
            con.execute(query)
        con.commit()

    def setUp(self):
        con = get_connection("mysql")
        con.execute("truncate table users")
        con.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        configure_close()
        for name, r in cls.results.items():
            print(name, r)

    def test_chunks_with_commit(self):
        CHUNK_SIZE = 10000
        query = """
            insert into users (id, name, email, amount) 
            values (%s, %s, %s, %s)"""

        con = get_connection("mysql")

        chunks = int(len(self.data) / CHUNK_SIZE)
        st = time.time()
        for i in range(chunks):
            con.executemany(
                query=query,
                data=self.data[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE],
            )
        con.commit()
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_big_query(self):
        con = get_connection("mysql")

        st = time.time()
        buffer = "insert into users (`id`, name, email, amount) values "
        buffer += ",".join(
            (
                f"({row[0]},'{row[1]}','{row[2]}','{row[3]}')"
                for row in self.data
            )
        )
        con.execute(buffer)
        con.commit()
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)


if __name__ == "__main__":
    # unittest.main(defaultTest=["TestPerformanceMySQL"])
    unittest.main()
