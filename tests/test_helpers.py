import unittest
from dataclasses import dataclass

from pydantic import BaseModel

from pydb.helpers import check_columns, check_sequence, extract_columns


class TestCheckColumns(unittest.TestCase):
    """Test cases for check_columns function"""

    def test_valid_columns_with_all_fields(self):
        """Test when columns match all fields and mandatory is subset of columns"""
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        # Should not raise
        check_columns(columns, mandatory, fields)

    def test_valid_columns_with_extra_fields(self):
        """Test when columns is subset of fields and mandatory is subset of columns"""
        columns = ["id", "name"]
        mandatory = ["id"]
        fields = ["id", "name", "email", "age"]
        # Should not raise
        check_columns(columns, mandatory, fields)

    def test_valid_with_single_mandatory(self):
        """Test with single mandatory column"""
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        # Should not raise
        check_columns(columns, mandatory, fields)

    def test_valid_with_empty_mandatory(self):
        """Test with empty mandatory columns"""
        columns = ["id", "name"]
        mandatory: list[str] = []
        fields = ["id", "name", "email"]
        # Should not raise
        check_columns(columns, mandatory, fields)

    def test_error_missing_mandatory_column(self):
        """Test error when mandatory column is missing from columns"""
        columns = ["id", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_columns(columns, mandatory, fields)
        self.assertIn(
            "columns must be superset of mandatory columns",
            str(context.exception),
        )
        self.assertIn("name", str(context.exception))

    def test_error_column_not_in_fields(self):
        """Test error when column is not in fields"""
        columns = ["id", "name", "phone"]
        mandatory = ["id"]
        fields = ["id", "name"]
        with self.assertRaises(AttributeError) as context:
            check_columns(columns, mandatory, fields)
        self.assertIn(
            "columns must be subset of all columns", str(context.exception)
        )
        self.assertIn("phone", str(context.exception))

    def test_error_multiple_missing_mandatory(self):
        """Test error with multiple missing mandatory columns"""
        columns = ["id"]
        mandatory = ["id", "name", "email"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_columns(columns, mandatory, fields)
        self.assertIn(
            "columns must be superset of mandatory columns",
            str(context.exception),
        )

    def test_error_multiple_columns_not_in_fields(self):
        """Test error with multiple columns not in fields"""
        columns = ["id", "phone", "address"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_columns(columns, mandatory, fields)
        self.assertIn(
            "columns must be subset of all columns", str(context.exception)
        )

    def test_both_errors_conditions_fail(self):
        """Test when both mandatory and column checks fail (mandatory check fails first)"""
        columns = ["id"]
        mandatory = ["id", "name"]
        fields = ["id", "email"]
        with self.assertRaises(AttributeError) as context:
            check_columns(columns, mandatory, fields)
        # First error should be about mandatory columns
        self.assertIn(
            "columns must be superset of mandatory columns",
            str(context.exception),
        )

    def test_with_tuples(self):
        """Test that function works with tuple sequences"""
        columns = ("id", "name", "email")
        mandatory = ("id", "name")
        fields = ("id", "name", "email", "age")
        # Should not raise
        check_columns(columns, mandatory, fields)


class TestExtractColumns(unittest.TestCase):
    """Test cases for extract_columns function"""

    def test_extract_from_dict(self):
        """Test extracting columns from a dictionary"""
        row = {"id": 1, "name": "John", "email": "john@example.com"}
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_extract_from_empty_dict(self):
        """Test extracting columns from an empty dictionary"""
        row: dict[str, object] = {}
        result = extract_columns(row)
        self.assertEqual(result, [])

    def test_extract_from_dataclass(self):
        """Test extracting columns from a dataclass"""

        @dataclass
        class User:
            id: int
            name: str
            email: str

        row = User(id=1, name="John", email="john@example.com")
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_extract_from_pydantic_model(self):
        """Test extracting columns from a Pydantic BaseModel"""

        class User(BaseModel):
            id: int
            name: str
            email: str

        row = User(id=1, name="John", email="john@example.com")
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_extract_from_simple_class(self):
        """Test extracting columns from a simple class instance"""

        class User:
            def __init__(self):
                self.id = 1
                self.name = "John"
                self.email = "john@example.com"

        row = User()
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_extract_from_class_filters_private_attrs(self):
        """Test that private attributes (starting with _) are filtered out"""

        class User:
            def __init__(self):
                self.id = 1
                self.name = "John"
                self._password = "secret"  # Should be filtered
                self.__dunder = "value"  # Should be filtered

        row = User()
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name"})
        self.assertNotIn("_password", result)
        self.assertNotIn("__dunder", result)

    def test_extract_from_class_filters_trailing_underscore(self):
        """Test that attributes ending with _ are filtered out"""

        class User:
            def __init__(self):
                self.id = 1
                self.name_ = "John"  # Should be filtered
                self.email = "john@example.com"

        row = User()
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "email"})
        self.assertNotIn("name_", result)

    def test_extract_from_class_with_mixed_attrs(self):
        """Test filtering with various attribute name patterns"""

        class User:
            def __init__(self):
                self.id = 1
                self.name = "John"
                self._private = "hidden"
                self._private_value = "also hidden"
                self.internal_ = "suffix filtered"
                self.__dunder__ = "both filtered"
                self.email_address = "john@example.com"  # Should be included

        row = User()
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "email_address"})

    def test_extract_error_on_unsupported_type(self):
        """Test that AttributeError is raised for unsupported types"""
        row = "unsupported_string"  # type: ignore
        with self.assertRaises(AttributeError) as context:
            extract_columns(row)
        self.assertIn("unknown row type", str(context.exception))

    def test_extract_error_on_list(self):
        """Test that AttributeError is raised for list type"""
        row = [1, 2, 3]  # type: ignore
        with self.assertRaises(AttributeError) as context:
            extract_columns(row)
        self.assertIn("unknown row type", str(context.exception))

    def test_extract_error_on_none(self):
        """Test that AttributeError is raised for None"""
        row = None  # type: ignore
        with self.assertRaises(AttributeError) as context:
            extract_columns(row)
        self.assertIn("unknown row type", str(context.exception))

    def test_extract_dict_with_various_types(self):
        """Test extracting dict with various value types"""
        row = {
            "id": 1,
            "name": "John",
            "active": True,
            "balance": 42.5,
            "tags": ["a", "b"],
        }
        result = extract_columns(row)
        self.assertEqual(
            set(result), {"id", "name", "active", "balance", "tags"}
        )

    def test_extract_dataclass_with_multiple_types(self):
        """Test extracting from dataclass with various field types"""

        @dataclass
        class User:
            id: int
            name: str
            active: bool
            balance: float

        row = User(id=1, name="John", active=True, balance=42.5)
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "active", "balance"})

    def test_extract_pydantic_with_multiple_types(self):
        """Test extracting from Pydantic model with various field types"""

        class User(BaseModel):
            id: int
            name: str
            active: bool
            balance: float

        row = User(id=1, name="John", active=True, balance=42.5)
        result = extract_columns(row)
        self.assertEqual(set(result), {"id", "name", "active", "balance"})


class TestCheckSequence(unittest.TestCase):
    """Test cases for check_sequence function"""

    # Tests with tuple/list rows
    def test_tuple_row_matches_columns_length(self):
        """Test tuple row with length matching columns"""
        row = (1, "John", "john@example.com")
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(result, ["id", "name", "email"])

    def test_list_row_matches_columns_length(self):
        """Test list row with length matching columns"""
        row = [1, "John", "john@example.com"]
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(result, ["id", "name", "email"])

    def test_tuple_row_matches_mandatory_length(self):
        """Test tuple row with length matching mandatory but not columns"""
        row = (1, "John")
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(result, ["id", "name"])

    def test_list_row_matches_mandatory_length(self):
        """Test list row with length matching mandatory but not columns"""
        row = [1, "John"]
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(result, ["id", "name"])

    def test_tuple_row_incorrect_length(self):
        """Test tuple row with length matching neither columns nor mandatory"""
        row = (1, "John", "john@example.com", "extra")
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email", "age"]
        with self.assertRaises(AttributeError) as context:
            check_sequence(row, columns, mandatory, fields)
        self.assertIn("incorrect row columns count", str(context.exception))
        self.assertIn("4", str(context.exception))

    def test_list_row_incorrect_length(self):
        """Test list row with invalid length"""
        row = [1]
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_sequence(row, columns, mandatory, fields)
        self.assertIn("incorrect row columns count", str(context.exception))

    # Tests with dict rows
    def test_dict_row_with_all_columns(self):
        """Test dict row containing all columns"""
        row = {"id": 1, "name": "John", "email": "john@example.com"}
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_dict_row_with_subset_of_columns(self):
        """Test dict row containing subset of columns"""
        row = {"id": 1, "name": "John"}
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name"})

    def test_dict_row_with_extra_fields(self):
        """Test dict row with columns not in fields (should fail validation)"""
        row = {"id": 1, "name": "John", "phone": "123"}
        columns = ["id", "name", "phone"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_sequence(row, columns, mandatory, fields)
        self.assertIn(
            "columns must be subset of all columns", str(context.exception)
        )

    def test_dict_row_missing_mandatory_column(self):
        """Test dict row without mandatory column"""
        row = {"id": 1}  # missing "name"
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_sequence(row, columns, mandatory, fields)
        self.assertIn(
            "row columns", str(context.exception)
        )  # Error from extract_columns check
        self.assertIn(
            "must be super set of mandatory columns", str(context.exception)
        )

    # Tests with dataclass rows
    def test_dataclass_row_valid(self):
        """Test dataclass row with valid data"""

        @dataclass
        class User:
            id: int
            name: str
            email: str

        row = User(id=1, name="John", email="john@example.com")
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_dataclass_row_subset_columns(self):
        """Test dataclass row with subset of columns"""

        @dataclass
        class User:
            id: int
            name: str
            email: str

        row = User(id=1, name="John", email="john@example.com")
        columns = ["id", "name"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name"})

    def test_dataclass_row_missing_mandatory(self):
        """Test dataclass row missing mandatory fields"""

        @dataclass
        class User:
            id: int
            email: str

        row = User(id=1, email="john@example.com")
        columns = ["id", "name", "email"]
        mandatory = ["id", "name"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_sequence(row, columns, mandatory, fields)
        self.assertIn(
            "must be super set of mandatory columns", str(context.exception)
        )

    # Tests with Pydantic model rows
    def test_pydantic_row_valid(self):
        """Test Pydantic model row with valid data"""

        class User(BaseModel):
            id: int
            name: str
            email: str

        row = User(id=1, name="John", email="john@example.com")
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_pydantic_row_subset_columns(self):
        """Test Pydantic model row with subset of columns"""

        class User(BaseModel):
            id: int
            name: str
            email: str

        row = User(id=1, name="John", email="john@example.com")
        columns = ["id", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "email"})

    # Tests with class instance rows
    def test_class_instance_row_valid(self):
        """Test class instance row with valid data"""

        class User:
            def __init__(self):
                self.id = 1
                self.name = "John"
                self.email = "john@example.com"

        row = User()
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name", "email"})

    def test_class_instance_row_with_extra_attributes(self):
        """Test class instance row with extra attributes"""

        class User:
            def __init__(self):
                self.id = 1
                self.name = "John"
                self.email = "john@example.com"
                self.phone = "123-456"

        row = User()
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email", "phone"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name", "email"})

    # Edge cases
    def test_empty_tuple_with_empty_mandatory(self):
        """Test empty tuple with empty mandatory columns"""
        row = ()
        columns = ["id", "name", "email"]
        mandatory: list[str] = []
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(result, [])

    def test_single_element_tuple(self):
        """Test single element tuple"""
        row = (1,)
        columns = ["id"]
        mandatory = ["id"]
        fields = ["id", "name"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(result, ["id"])

    def test_invalid_column_parameters_caught_first(self):
        """Test that invalid column parameters are caught before row validation"""
        row = (1, "John", "john@example.com")
        columns = ["id", "name", "phone"]  # "phone" not in fields
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        with self.assertRaises(AttributeError) as context:
            check_sequence(row, columns, mandatory, fields)
        # Should fail on columns validation, not row validation
        self.assertIn(
            "columns must be subset of all columns", str(context.exception)
        )

    def test_dict_with_intersection_of_columns(self):
        """Test dict row that only intersects with some columns"""
        row = {"id": 1, "name": "John"}
        columns = ["id", "name", "email"]
        mandatory = ["id"]
        fields = ["id", "name", "email"]
        result = check_sequence(row, columns, mandatory, fields)
        # Should return intersection of row columns and columns
        self.assertEqual(set(result), {"id", "name"})

    def test_row_with_more_fields_than_columns(self):
        """Test row with more fields than requested columns"""
        row = {
            "id": 1,
            "name": "John",
            "email": "john@example.com",
            "phone": "123",
        }
        columns = ["id", "name"]
        mandatory = ["id"]
        fields = ["id", "name", "email", "phone"]
        result = check_sequence(row, columns, mandatory, fields)
        self.assertEqual(set(result), {"id", "name"})


if __name__ == "__main__":
    unittest.main()
