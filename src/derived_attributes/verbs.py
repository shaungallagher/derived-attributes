import operator
from datetime import datetime, timedelta
from statistics import mean, median

import jsonata
from jsonpath_ng.ext import parse
from jsonpath_ng.ext.parser import ExtendedJsonPathLexer

# Necessary to support division operations
ExtendedJsonPathLexer.t_SORT_DIRECTION.__doc__ = r",?\s*(//|\\)"


def jsonpath_parse_val(dict_to_parse: dict, path: str):
    """
    Parse a path that matches a single scalar value, then return that value.
    """
    jsonpath_expr = parse(path)
    return next(iter(match.value for match in jsonpath_expr.find(dict_to_parse)), None)


def jsonpath_parse_list(dict_to_parse: dict, path: str):
    """
    Parse a path that matches a list of values, then return that list.
    """
    jsonpath_expr = parse(path)
    return [match.value for match in jsonpath_expr.find(dict_to_parse)]


def parse_jsonata(dict_to_parse: dict, query: str):
    """
    Parse a query in Jsonata syntax and evaluate it against the dict.
    """
    expr = jsonata.Jsonata(query)
    result = expr.evaluate(dict_to_parse)
    return result


# The functions to call for each verb.
VERB_FUNCTIONS = {
    "parse_jsonata": parse_jsonata,
    "parse": jsonpath_parse_val,
    "parse_list": jsonpath_parse_list,
    ">": lambda x, y: operator.gt(float(x), float(y)),
    "<": lambda x, y: operator.lt(float(x), float(y)),
    "=": lambda x, y: operator.eq(float(x), float(y)),
    "!=": lambda x, y: not operator.eq(float(x), float(y)),
    "eq": lambda x, y: operator.eq(x, y),
    "neq": lambda x, y: not operator.eq(x, y),
    "and": lambda x, y: x and y,
    "or": lambda x, y: x or y,
    "len": lambda x, _: len(x),
    "sum": lambda x, _: sum(x),
    "min": lambda x, _: min(x),
    "max": lambda x, _: max(x),
    "median": lambda x, _: median(x),
    "parse_len": lambda x, y: len(jsonpath_parse_list(x, y)),
    "parse_sum": lambda x, y: sum(jsonpath_parse_list(x, y)),
    "parse_min": lambda x, y: min(jsonpath_parse_list(x, y)),
    "parse_max": lambda x, y: max(jsonpath_parse_list(x, y)),
    "parse_mean": lambda x, y: mean(jsonpath_parse_list(x, y)),
    "parse_median": lambda x, y: median(jsonpath_parse_list(x, y)),
    "list_divide": lambda x, y: [float(a) / float(b) for a, b in zip(x, y)],
    "within_last_days": lambda x, y: datetime.today() - x <= timedelta(days=int(y)),
    "list_within_last_days": lambda x, y: [
        item for item in x if datetime.today() - item <= timedelta(days=int(y))
    ],
}

# A subset of verbs require evaluation of both the
# subject and object before the verb function can run.
JOINING_VERBS = [
    "and",
    "or",
    "list_divide",
]

# Verbs that require an object with valid Jsonpath syntax
JSONPATH_VERBS = [
    "parse",
    "parse_list",
    "parse_len",
    "parse_sum",
    "parse_min",
    "parse_max",
    "parse_mean",
    "parse_median",
]
