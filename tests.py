from derive import DeriveAttributes, Sentence


class TestClass:

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
            Sentence(
                "test_sum",
                "_parse_list",
                "sum",
                None
            ),
            Sentence(
                "test_min",
                "_parse_list",
                "min",
                None
            ),
            Sentence(
                "test_max",
                "_parse_list",
                "max",
                None
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
            "test_len": 2,
            "test_sum": 90,
            "test_min": 40,
            "test_max": 50,
        }
        assert results == expected
