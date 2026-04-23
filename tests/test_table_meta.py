import unittest
from typing import Set

from pydb.tablemeta import TableField, TableMetaData
from src.pydb import configure, configure_close, get_connection
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

    @classmethod
    def tearDownClass(cls) -> None:
        configure_close()

    def test_read(self):
        for name in ["psql", "mysql"]:
            with self.subTest(name):
                con = get_connection(name)
                table = con.table_metadata("test_metadata")

                self.assertEqual(table.name, "test_metadata")
                self.assertEqual(len(table.fields), 5)
                self.assertEqual(table.fields["id"].field_type, "int")
                self.assertEqual(table.fields["id"].is_pk, True)
                self.assertEqual(table.fields["name"].field_type, "varchar")
                self.assertEqual(table.fields["name"].is_pk, True)
                self.assertEqual(
                    table.fields["name"].default_value,
                    "name",
                    table.fields["name"].default_value,
                )
                self.assertEqual(
                    table.fields["value_float"].field_type, "decimal"
                )
                self.assertEqual(table.fields["value_float"].is_pk, False)
                self.assertEqual(table.fields["value_float"].is_not_null, False)
                self.assertEqual(table.fields["value_float"].size, (10, 2))

                if name == "psql":
                    self.assertEqual(
                        table.fields["camelCase"].field_type, "int"
                    )
                if name == "msql":
                    self.assertEqual(
                        table.fields["camelCase"].field_type, "int"
                    )

    def test_cache(self):
        ids: dict[str, Set[int]] = {}

        for name in CONFIGS.root:
            con = get_connection(name)
            s = ids.setdefault(name, set())
            s.add(id(con.table_metadata("test_metadata")))
            s.add(id(con.table_metadata("test_metadata")))

        self.assertEqual(len(ids), 2, ids)
        for name, s in ids.items():
            with self.subTest(name):
                self.assertEqual(len(s), 1, s)


class TestTableMetaDataMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:

        cls.meta = TableMetaData(name="name", db_name="data")
        cls.meta.fields["id"] = TableField(
            name="id", is_ai=True, is_not_null=True
        )
        cls.meta.fields["name"] = TableField(name="name", is_not_null=True)
        cls.meta.fields["email"] = TableField(
            name="email", is_not_null=True, default_value="email"
        )
        cls.meta.fields["address"] = TableField(name="address")

    def test_mandatory(self):

        res = self.meta.mandatory()
        self.assertEqual(set(res), {"name"}, res)

    def test_not_null(self):

        res = self.meta.not_null()
        self.assertEqual(set(res), {"name", "id", "email"}, res)


if __name__ == "__main__":
    unittest.main()
