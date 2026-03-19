import inspect
import random
import time
import unittest
from dataclasses import asdict
from decimal import Decimal
from typing import Any, Tuple, cast

from pydbio.basicio import configure, get_connection
from pydbio.pgio import PSQL, PSQLConnection, ThreadedConnectionPool
from tests.config import CONFIGS


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


POOL: ThreadedConnectionPool | None = None


def open_connection_pool():
    global POOL
    if POOL is not None:
        return

    kwargs = asdict(CONFIGS["psql"])
    kwargs.pop("dialect")

    POOL = ThreadedConnectionPool(minconn=4, maxconn=10, **kwargs)


def getconn(key: str | None = None) -> PSQLConnection:
    global POOL
    if POOL is None:
        raise RuntimeError("call open_connection_pool first")

    return POOL.getconn(key)


def putconn(con: PSQLConnection, key: str | None = None):
    global POOL
    if POOL is None:
        raise RuntimeError("call open_connection_pool first")

    POOL.putconn(con, key)


class TestPerformance(unittest.TestCase):
    data: list[Any] = []
    results: dict[str, str] = {}

    @classmethod
    def setUpClass(cls) -> None:
        configure(CONFIGS)

        cls.data = gen_data_set(1000000)
        cls.results = {}

    def setUp(self):
        con = get_connection("psql")
        con.execute("truncate table users")
        con.commit()

    @classmethod
    def tearDownClass(cls) -> None:
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

    def test_connection_pool(self):
        ITERATIONS = 1000
        open_connection_pool()

        st = time.time()
        for i in range(ITERATIONS):
            con = getconn()
            with con.cursor() as cur:
                cur.execute("select 1+1")
                cur.fetchall()
            putconn(con)
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)

    def test_connection(self):
        ITERATIONS = 1000
        con = PSQL(config=CONFIGS["psql"])

        st = time.time()
        for i in range(ITERATIONS):
            con.fetch_tuples("select 1+1")
        fn = time.time()

        name = inspect.stack()[0][3]
        self.results[name] = format_time(fn - st)


if __name__ == "__main__":
    unittest.main(
        defaultTest=[
            "TestPerformance.test_connection_pool",
            "TestPerformance.test_connection",
        ]
    )
    # unittest.main()
