import unittest

from src.pydb import configure, get_connection
from tests.config import CONFIGS, TABLE_METADATA


class TestTableMetaData(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configure(CONFIGS.root)
        for name, values in TABLE_METADATA.items():
            con = get_connection(name)
            for value in values:
                con.execute(value)
                con.commit()

    def test_read(self):
        for name in ["psql", "mysql"]:
            with self.subTest(name):
                con = get_connection(name)
                table = con.table_metadata("test_metadata")

                self.assertEqual(table.name, "test_metadata")
                self.assertEqual(len(table.fields), 4)
                self.assertEqual(table.fields["id"].field_type, "int")
                self.assertEqual(table.fields["id"].is_pk, True)
                self.assertEqual(table.fields["name"].field_type, "varchar")
                self.assertEqual(table.fields["name"].is_pk, True)
                self.assertEqual(
                    table.fields["value_float"].field_type, "decimal"
                )
                self.assertEqual(table.fields["value_float"].is_pk, False)
                self.assertEqual(table.fields["value_float"].is_not_null, False)
                self.assertEqual(table.fields["value_float"].size, (10, 2))


if __name__ == "__main__":
    unittest.main()
