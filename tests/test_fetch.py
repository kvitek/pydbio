import unittest
from dataclasses import dataclass

from pydantic import BaseModel

from pydbio.basicio import configure, get_connection
from tests.config import CONFIGS


@dataclass
class Company:
    cik: int
    company_name: str
    sic: int
    addres: str = ""


class CompanyModel(BaseModel):
    cik: int
    company_name: str
    sic: int
    addres: str = ""


class TestDataclassFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        configure(CONFIGS)

    def test(self):
        con = get_connection("mysql")
        data = con.fetch_typed(
            Company,
            "select cik, sic, company_name from companies limit 10",
        )
        self.assertEqual(len(data), 10, data)

    def test_base_model(self):
        con = get_connection("mysql")

        with self.subTest("normal"):
            data = con.fetch_typed_pydantic(
                CompanyModel,
                "select cik, sic, company_name from companies limit 10",
            )
            self.assertEqual(len(data), 10, data)

        with self.subTest("raise on wrong class"):
            with self.assertRaises(AttributeError):
                data = con.fetch_typed_pydantic(
                    Company,  # type: ignore
                    "select cik, sic, company_name from companies limit 10",
                )

        with self.subTest("raise on wrong header"):
            with self.assertRaises(RuntimeError):
                data = con.fetch_typed_pydantic(
                    CompanyModel,
                    "select cik, company_name from companies limit 10",
                )

    def test_find_all(self):
        con = get_connection("mysql")

        data = con.find_all(
            Company, "companies", {"cik": ("<", 1000)}, all=False
        )

        print(data[:10])


if __name__ == "__main__":
    unittest.main()
