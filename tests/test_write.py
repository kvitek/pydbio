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
    def __init__(
        self, id: int, name: str, email: str, amount: Decimal = Decimal(0)
    ):
        self.id = id
        self.name = name
        self.email = email
        self.amount = amount


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

    def test_insert_update_tuples(self):
        for name in CONFIGS.root:
            con = get_connection(name)
            with self.subTest(f"`{name}`: raise"):
                with self.assertRaises(RuntimeError):
                    con.insert_update(
                        data=[(1, "name", "email")],
                        table_name="users",
                        columns=["id", "name", "email"],
                    )

            with self.subTest(f"`{name}`: update"):
                con.insert_update(
                    data=[(1, "name", "email", Decimal(101))],
                    table_name="users",
                    columns=["id", "name", "email", "amount"],
                )

                params, where = con.where({"id": 1})
                data = con.fetch_dict(
                    f"select * from users where {where}", params=params
                )
                self.assertEqual(len(data), 1)
                self.assertDictEqual(
                    data[0],
                    {
                        "id": 1,
                        "name": "name",
                        "email": "email",
                        "amount": Decimal(101),
                    },
                )

                con.rollback()

            with self.subTest(f"`{name}`: insert"):
                con.insert_update(
                    data=[(100, "name", "email", Decimal(101))],
                    table_name="users",
                    columns=["id", "name", "email", "amount"],
                )

                params, where = con.where({"id": 100})
                data = con.fetch_dict(
                    f"select * from users where {where}", params=params
                )
                self.assertEqual(len(data), 1)
                self.assertDictEqual(
                    data[0],
                    {
                        "id": 100,
                        "name": "name",
                        "email": "email",
                        "amount": Decimal(101),
                    },
                )
                con.rollback()

    def test_insert_update_dict(self):
        for name in CONFIGS.root:
            con = get_connection(name)
            with self.subTest(f"`{name}`: raise"):
                with self.assertRaises(Exception):
                    con.insert_update(
                        data=[{"id": 1, "name": "name", "email": "email"}],
                        table_name="users",
                    )

            with self.subTest(f"`{name}`: update"):
                con.insert_update(
                    data=[
                        {
                            "id": 1,
                            "name": "name",
                            "email": "email",
                            "amount": Decimal(101),
                        }
                    ],
                    table_name="users",
                    columns=["id", "name", "email", "amount"],
                )

                params, where = con.where({"id": 1})
                data = con.fetch_dict(
                    f"select * from users where {where}", params=params
                )
                self.assertEqual(len(data), 1)
                self.assertDictEqual(
                    data[0],
                    {
                        "id": 1,
                        "name": "name",
                        "email": "email",
                        "amount": Decimal(101),
                    },
                )
                con.rollback()

            with self.subTest(f"`{name}`: insert"):
                con.insert_update(
                    data=[
                        {
                            "id": 100,
                            "name": "name",
                            "email": "email",
                            "amount": Decimal(101),
                        }
                    ],
                    table_name="users",
                    columns=["id", "name", "email", "amount"],
                )

                params, where = con.where({"id": 100})
                data = con.fetch_dict(
                    f"select * from users where {where}", params=params
                )
                self.assertEqual(len(data), 1)
                self.assertDictEqual(
                    data[0],
                    {
                        "id": 100,
                        "name": "name",
                        "email": "email",
                        "amount": Decimal(101),
                    },
                )
                con.rollback()

    def test_insert_update_object(self):
        for name in CONFIGS.root:
            con = get_connection(name)
            with self.subTest(f"`{name}`: update"):
                con.insert_update(
                    data=[User(1, "name", "email", Decimal(101))],
                    table_name="users",
                    columns=["id", "name", "email", "amount"],
                )

                params, where = con.where({"id": 1})
                data = con.fetch_dict(
                    f"select * from users where {where}", params=params
                )
                self.assertEqual(len(data), 1)
                self.assertDictEqual(
                    data[0],
                    {
                        "id": 1,
                        "name": "name",
                        "email": "email",
                        "amount": Decimal(101),
                    },
                )
                con.rollback()

            with self.subTest(f"`{name}`: insert"):
                con.insert_update(
                    data=[User(100, "name", "email", Decimal(101))],
                    table_name="users",
                    columns=["id", "name", "email", "amount"],
                )

                params, where = con.where({"id": 100})
                data = con.fetch_dict(
                    f"select * from users where {where}", params=params
                )
                self.assertEqual(len(data), 1)
                self.assertDictEqual(
                    data[0],
                    {
                        "id": 100,
                        "name": "name",
                        "email": "email",
                        "amount": Decimal(101),
                    },
                )
                con.rollback()


if __name__ == "__main__":
    unittest.main()
