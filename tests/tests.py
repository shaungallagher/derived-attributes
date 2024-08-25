import pytest
from pydantic import ValidationError

from src.derived_attributes.derive import (
    DeriveAttributes,
    DeriveRules,
    DeriveTriggers,
    InputBuilder,
    Sentence,
    Trigger,
)


class TestInputBuilder:
    def test_from_list_of_dicts_validation_success(self):
        input = [
            {
                "attr": "test_name",
                "subject": "source",
                "verb": "parse_max",
                "obj": "$.records[*].vendors[?has_contract == true].budget",
            },
            {
                "attr": "test_name2",
                "subject": "source",
                "verb": "sum",
                "obj": None,
            },
        ]

        InputBuilder.from_list_of_dicts(input)

    def test_from_list_of_dicts_validation_error(self):
        input = [
            {
                "attr.invalid": "test_name",
                "subject.invalid": "test_subject",
                "obj.invalid": "test_obj",
            },
            {
                "attr": 123,
                "subject": 456,
                "verb": None,
                "obj": 789,
            },
        ]

        with pytest.raises(ValidationError):
            InputBuilder.from_list_of_dicts(input)

    def test_from_csv_validation_success(self):
        input = (
            "attr,subject,verb,obj"
            "test_name,source,parse_max,$.records[*].vendors[?has_contract == true].budget",
            "test_name2,source,sum,",
        )

        InputBuilder.from_csv(input)

    def test_from_csv_validation_error(self):
        input = (
            "attr.invalid,subject.invalid,obj.invalid"
            "test_name,test_subject,test_obj",
            "123,456,789",
        )

        with pytest.raises(ValidationError):
            InputBuilder.from_csv(input)


class TestDeriveAttributes:
    def test_readme_example(self):
        sentences = [
            Sentence(
                "total_vendor_count", "source", "parse_len", "$.records[*].vendors[*]"
            ),
            Sentence(
                "max_budget_only_contract",
                "source",
                "parse_max",
                "$.records[*].vendors[?has_contract == true].budget",
            ),
            Sentence(
                "_used_budget",
                "source",
                "parse_list",
                "$.records[*].vendors[*].expenses / $.records[*].vendors[*].budget",
            ),
            Sentence("median_used_budget", "_used_budget", "median", None),
        ]
        source = {
            "records": [
                {
                    "business_name": "ABC Electronics",
                    "vendors": [
                        {
                            "vendor_name": "Tech Solutions",
                            "has_contract": False,
                            "budget": 15000,
                            "expenses": 8000,
                        },
                        {
                            "vendor_name": "Office Supplies Inc.",
                            "has_contract": True,
                            "budget": 2000,
                            "expenses": 1500,
                        },
                    ],
                },
                {
                    "business_name": "XYZ Marketing",
                    "vendors": [
                        {
                            "vendor_name": "AdvertiseNow",
                            "has_contract": True,
                            "budget": 10000,
                            "expenses": 9000,
                        },
                        {
                            "vendor_name": "Print House",
                            "has_contract": True,
                            "budget": 3000,
                            "expenses": 3000,
                        },
                    ],
                },
            ]
        }
        da = DeriveAttributes(sentences, source)
        results = da.derive()
        expected = {
            "total_vendor_count": 4,
            "max_budget_only_contract": 10000,
            "median_used_budget": 0.825,
        }
        assert results == expected

    def test_parse_verbs(self):
        sentences = [
            Sentence("test_parse_str", "source", "parse", "$.test_str"),
            Sentence("test_parse_int", "source", "parse", "$.test_int"),
            Sentence("test_parse_float", "source", "parse", "$.test_float"),
            Sentence("test_parse_len", "source", "parse_len", "$.test_list[*]"),
            Sentence("test_parse_sum", "source", "parse_sum", "$.test_list[*]"),
            Sentence("test_parse_min", "source", "parse_min", "$.test_list[*]"),
            Sentence("test_parse_max", "source", "parse_max", "$.test_list[*]"),
        ]
        source = {
            "test_str": "lucky",
            "test_int": 42,
            "test_float": 3.1415,
            "test_list": [1, 2, 3, 4, 5],
        }
        da = DeriveAttributes(sentences, source)
        results = da.derive()
        expected = {
            "test_parse_str": "lucky",
            "test_parse_int": 42,
            "test_parse_float": 3.1415,
            "test_parse_len": 5,
            "test_parse_sum": 15,
            "test_parse_min": 1,
            "test_parse_max": 5,
        }
        assert results == expected

    def test_parse_list(self):
        sentences = [
            Sentence(
                "test_parse_list_filter_gt",
                "source",
                "parse_list",
                "$.test_list_of_dicts[?age > 35].name",
            ),
            Sentence(
                "test_parse_list_filter_lt",
                "source",
                "parse_list",
                "$.test_list_of_dicts[?age < 45].name",
            ),
            Sentence(
                "test_parse_list_filter_eq",
                "source",
                "parse_list",
                "$.test_list_of_dicts[?age = 40].name",
            ),
        ]
        source = {
            "test_list_of_dicts": [
                {
                    "name": "Alice",
                    "age": 30,
                },
                {
                    "name": "Bob",
                    "age": 40,
                },
                {
                    "name": "Cindy",
                    "age": 50,
                },
            ]
        }
        da = DeriveAttributes(sentences, source)
        results = da.derive()
        expected = {
            "test_parse_list_filter_gt": ["Bob", "Cindy"],
            "test_parse_list_filter_lt": ["Alice", "Bob"],
            "test_parse_list_filter_eq": ["Bob"],
        }
        assert results == expected

    def test_list_ops(self):
        sentences = [
            Sentence(
                "_parse_list",
                "source",
                "parse_list",
                "$.test_list_of_dicts[?age > 35].age",
            ),
            Sentence(
                "test_len",
                "_parse_list",
                "len",
                None,
            ),
            Sentence("test_sum", "_parse_list", "sum", None),
            Sentence("test_min", "_parse_list", "min", None),
            Sentence("test_max", "_parse_list", "max", None),
        ]
        source = {
            "test_list_of_dicts": [
                {
                    "name": "Alice",
                    "age": 30,
                },
                {
                    "name": "Bob",
                    "age": 40,
                },
                {
                    "name": "Cindy",
                    "age": 50,
                },
            ]
        }
        da = DeriveAttributes(sentences, source)
        results = da.derive()
        expected = {
            "test_len": 2,
            "test_sum": 90,
            "test_min": 40,
            "test_max": 50,
        }
        assert results == expected

    def test_parse_jsonata_syntax(self):
        sentences = [
            Sentence(
                "total_expenses",
                "source",
                "parse_jsonata",
                "$sum(records.vendors.expenses)",
            ),
            Sentence(
                "remaining_budget",
                "source",
                "parse_jsonata",
                "$sum(records.vendors.(budget - expenses))",
            ),
            Sentence(
                "has_contract_booleans",
                "source",
                "parse_jsonata",
                (
                    "(records[0].vendors[0].has_contract) or "
                    "(records[1].vendors[0].has_contract = "
                    "records[1].vendors[1].has_contract)"
                ),
            ),
        ]
        source = {
            "records": [
                {
                    "business_name": "ABC Electronics",
                    "vendors": [
                        {
                            "vendor_name": "Tech Solutions",
                            "has_contract": False,
                            "budget": 15000,
                            "expenses": 8000,
                        },
                        {
                            "vendor_name": "Office Supplies Inc.",
                            "has_contract": True,
                            "budget": 2000,
                            "expenses": 1500,
                        },
                    ],
                },
                {
                    "business_name": "XYZ Marketing",
                    "vendors": [
                        {
                            "vendor_name": "AdvertiseNow",
                            "has_contract": True,
                            "budget": 10000,
                            "expenses": 9000,
                        },
                        {
                            "vendor_name": "Print House",
                            "has_contract": True,
                            "budget": 3000,
                            "expenses": 3000,
                        },
                    ],
                },
            ]
        }
        da = DeriveAttributes(sentences, source)
        results = da.derive()

        expected = {
            "total_expenses": 21500,
            "remaining_budget": 8500,
            "has_contract_booleans": True,
        }

        assert results == expected


class TestDeriveRules:
    def test_all_rules_pass(self):
        sentences = [
            Sentence("_vendor_count", "source", "parse_len", "$.records[*].vendors[*]"),
            Sentence("has_multiple_vendors", "_vendor_count", ">", 1),
            Sentence("_record_count", "source", "parse_len", "$.records[*]"),
            Sentence("has_multiple_records", "_record_count", ">", 1),
        ]
        source = {
            "records": [
                {
                    "business_name": "ABC Electronics",
                    "vendors": [
                        {
                            "vendor_name": "Tech Solutions",
                            "has_contract": False,
                            "budget": 15000,
                            "expenses": 8000,
                        },
                        {
                            "vendor_name": "Office Supplies Inc.",
                            "has_contract": True,
                            "budget": 2000,
                            "expenses": 1500,
                        },
                    ],
                },
                {
                    "business_name": "XYZ Marketing",
                    "vendors": [
                        {
                            "vendor_name": "AdvertiseNow",
                            "has_contract": True,
                            "budget": 10000,
                            "expenses": 9000,
                        },
                        {
                            "vendor_name": "Print House",
                            "has_contract": True,
                            "budget": 3000,
                            "expenses": 3000,
                        },
                    ],
                },
            ]
        }
        da = DeriveRules(sentences, source)
        results = da.derive()

        all_rules_pass = all(results)
        assert all_rules_pass is True


class TestDeriveTriggers:
    def test_all_triggers_fire(self, mocker):
        triggers = [
            Trigger("_source_id", "source", "parse", "$.source_id"),
            Trigger("_vendor_count", "source", "parse_len", "$.records[*].vendors[*]"),
            Trigger(
                "has_multiple_vendors",
                "_vendor_count",
                ">",
                1,
                "do_something",
                ["_source_id"],
            ),
            Trigger("_record_count", "source", "parse_len", "$.records[*]"),
            Trigger(
                "has_multiple_records",
                "_record_count",
                ">",
                1,
                "do_something_else",
                ["_source_id"],
            ),
        ]
        source = {
            "source_id": "123-789",
            "records": [
                {
                    "business_name": "ABC Electronics",
                    "vendors": [
                        {
                            "vendor_name": "Tech Solutions",
                            "has_contract": False,
                            "budget": 15000,
                            "expenses": 8000,
                        },
                        {
                            "vendor_name": "Office Supplies Inc.",
                            "has_contract": True,
                            "budget": 2000,
                            "expenses": 1500,
                        },
                    ],
                },
                {
                    "business_name": "XYZ Marketing",
                    "vendors": [
                        {
                            "vendor_name": "AdvertiseNow",
                            "has_contract": True,
                            "budget": 10000,
                            "expenses": 9000,
                        },
                        {
                            "vendor_name": "Print House",
                            "has_contract": True,
                            "budget": 3000,
                            "expenses": 3000,
                        },
                    ],
                },
            ],
        }

        mock_event_handler = mocker.MagicMock()

        da = DeriveTriggers(triggers, source, mock_event_handler)

        da.derive()

        assert mock_event_handler.call_count == 2

        mock_event_handler.assert_any_call("do_something", "123-789")
        mock_event_handler.assert_any_call("do_something_else", "123-789")
