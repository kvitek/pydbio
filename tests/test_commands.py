import unittest

from pydb.basicio import get_connection
from pydb.commands import gen_table_name
from tests.config import TABLE_METADATA


class TestCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        for name, values in TABLE_METADATA.items():
            con = get_connection(name)
            for value in values:
                con.execute(value)
                con.commit()

    def test_gen_name(self):
        with self.subTest('sep = `"`'):
            cmd = gen_table_name("myTableName", sep='"')
            self.assertEqual(cmd, '"myTableName"')

        with self.subTest("sep = `'`"):
            cmd = gen_table_name("my_table_name", db_name="public", sep="'")
            self.assertEqual(cmd, "'public'.'my_table_name'")

    def test_insert(self):
        con = get_connection("psql")
        cmd = """
            insert into test_metadata (id, name) values (%(id)s, %(name)s)
"""
        con.executemany(cmd, [{"id": 1, "name": "name1"}])
        con.commit()


if __name__ == "__main__":
    unittest.main()
