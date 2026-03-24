import unittest
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel

from src.pydb.basicio import configure, configure_close, get_connection
from tests.config import CONFIGS, TEST_TABLES


@dataclass
class UserDC:
    id: int
    name: str
    email: str
    amount: Decimal = Decimal(0)


class UserBM(BaseModel):
    id: int
    name: str
    email: str
    amount: Decimal = Decimal(0)


class User:
    pass


class TestDataclassFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        configure(CONFIGS.root)

        insert = "insert into users (id, name, email, amount) values (%s, %s, %s, %s)"
        data = [
            (i + 1, f"user name {i}", f"email{i}@example.com", 100 + i * 10)
            for i in range(10)
        ]

        for name, queries in TEST_TABLES.items():
            c = get_connection(name)
            for q in queries:
                c.execute(q)

            c.executemany(insert, data)
            c.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

        configure_close()

    def test(self):
        con = get_connection("mysql")
        data = con.fetch_typed(
            UserDC,
            "select id, name, email, amount from users limit 10",
        )
        self.assertEqual(len(data), 10, data)

    def test_base_model(self):
        con = get_connection("mysql")

        with self.subTest("normal"):
            data = con.fetch_typed(
                UserBM,
                "select id, name, email, amount from users limit 10",
            )
            self.assertEqual(len(data), 10, data)

        with self.subTest("raise on wrong class"):
            with self.assertRaises(AttributeError):
                data = con.fetch_typed(
                    User,  # type: ignore
                    "select id, name, email, amount from users limit 10",
                )

        with self.subTest("raise on wrong header"):
            with self.assertRaises(RuntimeError):
                data = con.fetch_typed(
                    UserBM,
                    "select id, name, amount from users limit 10",
                )

    def test_find_all(self):
        con = get_connection("mysql")

        data = con.find_all(UserDC, "users", {"id": ("<", 5)}, all=False)

        self.assertEqual(len(data), 4, msg=data)


if __name__ == "__main__":
    unittest.main()
