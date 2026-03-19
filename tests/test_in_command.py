import unittest

from pydbio.helpers import parse_dict_command, parse_positional_command


class TestInCommand(unittest.TestCase):
    def test_positional(self):
        params = [100, 200]
        params_in = [1, 2]

        with self.subTest("regular"):
            query = "select * from comapnies where cik=%s and sic in (__in__) and id = %s"
            new_query, new_params = parse_positional_command(
                query, params, params_in
            )

            self.assertEqual(
                new_query,
                "select * from comapnies where cik=%s and sic in (%s,%s) and id = %s",
            )
            self.assertEqual(new_params, [100, 1, 2, 200])

        with self.subTest("dict first"):
            query = "select * from comapnies where cik=%s and id = %s and sic in (__in__)"
            new_query, new_params = parse_positional_command(
                query, params, params_in
            )

            self.assertEqual(
                new_query,
                "select * from comapnies where cik=%s and id = %s and sic in (%s,%s)",
            )
            self.assertEqual(new_params, [100, 200, 1, 2])

        with self.subTest("dict last"):
            query = "select * from comapnies where sic in (__in__) and cik=%s and id = %s"
            new_query, new_params = parse_positional_command(
                query, params, params_in
            )

            self.assertEqual(
                new_query,
                "select * from comapnies where sic in (%s,%s) and cik=%s and id = %s",
            )
            self.assertEqual(new_params, [1, 2, 100, 200])

        with self.subTest("no (__in__)"):
            query = "select * from comapnies where cik=%s and id = %s"
            new_query, new_params = parse_positional_command(
                query, params, params_in
            )

            self.assertEqual(
                new_query,
                "select * from comapnies where cik=%s and id = %s",
            )
            self.assertEqual(new_params, [100, 200])

    def test_dictionary(self):
        params = {"cik": 100, "id": 200}
        params_in = [1, 2]

        with self.subTest("regular"):
            query = "select * from comapnies where cik=%(cik)s and sic in (__in__) and id = %(id)s"
            new_query, new_params = parse_dict_command(query, params, params_in)

            self.assertEqual(
                new_query,
                "select * from comapnies where cik=%s and sic in (%s,%s) and id = %s",
            )
            self.assertEqual(new_params, [100, 1, 2, 200])

        with self.subTest("dict first"):
            query = "select * from comapnies where cik=%(cik)s and id = %(id)s and sic in (__in__)"
            new_query, new_params = parse_dict_command(query, params, params_in)

            self.assertEqual(
                new_query,
                "select * from comapnies where cik=%s and id = %s and sic in (%s,%s)",
            )
            self.assertEqual(new_params, [100, 200, 1, 2])

        with self.subTest("dict last"):
            query = "select * from comapnies where sic in (__in__) and cik=%(cik)s and id = %(id)s"
            new_query, new_params = parse_dict_command(query, params, params_in)

            self.assertEqual(
                new_query,
                "select * from comapnies where sic in (%s,%s) and cik=%s and id = %s",
            )
            self.assertEqual(new_params, [1, 2, 100, 200])

        with self.subTest("no (__in__)"):
            query = "select * from comapnies where cik=%(cik)s and id = %(id)s"
            new_query, new_params = parse_dict_command(query, params, params_in)

            self.assertEqual(
                new_query,
                "select * from comapnies where cik=%s and id = %s",
            )
            self.assertEqual(new_params, [100, 200])


if __name__ == "__main__":
    unittest.main()
