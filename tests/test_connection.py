import unittest

from pydbio.basicio import configure, get_connection
from tests.config import CONFIGS


class TestConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configure(CONFIGS)

    def test_con_reconnect(self):
        for name in ["mysql", "psql"]:
            with self.subTest(name):
                con = get_connection(name)

                data = con.fetch_tuples("select 1")
                self.assertTrue(len(data) > 0)

                with self.assertRaises(Exception):
                    data = con.fetch_tuples("select * from unknown limit 10")

                data = con.fetch_tuples("select 1")
                self.assertTrue(len(data) > 0)

    def test_connection_closed(self):
        for name in ["mysql", "psql"]:
            with self.subTest(name):
                con = get_connection(name)

                data = con.fetch_tuples("select 1")
                self.assertTrue(len(data) > 0)

                con.close()

                data = con.fetch_tuples("select 1")
                self.assertTrue(len(data) > 0)


if __name__ == "__main__":
    # unittest.main(defaultTest="TestConnection.test_connection_closed")
    unittest.main()
