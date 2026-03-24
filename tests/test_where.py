import unittest

from pydb.where import gen_where


class TestWhere(unittest.TestCase):
    def test(self):
        with self.subTest("top logical"):
            params, where = gen_where(
                {
                    "cik": 100,
                    "company_name": ("like", "%apple%"),
                    "sic": ("in", [100, 200]),
                    "or": {
                        "field": "abc",
                        "field1": 100,
                    },
                }
            )
            self.assertEqual(
                params, [100, "%apple%", 100, 200, "abc", 100], params
            )
            self.assertEqual(
                where,
                "(cik = %s) and (company_name like %s) and (sic in (%s,%s)) and ((field = %s) or (field1 = %s))",
                where,
            )

        with self.subTest("default `and` as top"):
            params, where = gen_where(
                {
                    "cik": 100,
                    "company_name": ("like", "%apple%"),
                    "sic": ("in", [100, 200]),
                }
            )
            self.assertEqual(params, [100, "%apple%", 100, 200], params)
            self.assertEqual(
                where,
                "(cik = %s) and (company_name like %s) and (sic in (%s,%s))",
                where,
            )

        with self.subTest("nested `or`"):
            params, where = gen_where(
                {
                    "cik": 100,
                    "company_name": ("like", "%apple%"),
                    "or": {"sic": ("in", [100, 200]), "field": "100"},
                }
            )
            self.assertEqual(params, [100, "%apple%", 100, 200, "100"], params)
            self.assertEqual(
                where,
                "(cik = %s) and (company_name like %s) and ((sic in (%s,%s)) or (field = %s))",
                where,
            )

        with self.subTest("`not`"):
            params, where = gen_where(
                {"not": {"and": {"cik": 100, "company_name": ("like", "%app")}}}
            )
            self.assertEqual(params, [100, "%app"], params)
            self.assertEqual(
                where, "(not ((cik = %s) and (company_name like %s)))", where
            )

        with self.subTest("`<=`"):
            params, where = gen_where(
                {"cik": ("<=", 100), "company_name": ("like", "%app")}
            )
            self.assertEqual(params, [100, "%app"], params)
            self.assertEqual(
                where, "(cik <= %s) and (company_name like %s)", where
            )

        with self.subTest("`==`"):
            params, where = gen_where(
                {"cik": ("==", "cik"), "company_name": ("like", "%app")}
            )
            self.assertEqual(params, ["%app"], params)
            self.assertEqual(
                where, "(cik = cik) and (company_name like %s)", where
            )


if __name__ == "__main__":
    unittest.main()
