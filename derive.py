import operator
from dataclasses import dataclass
from datetime import date, timedelta
import json
from statistics import median
from typing import Any, Callable, List, Optional

from jsonpath_ng.ext import parse
from jsonpath_ng.ext.parser import ExtendedJsonPathLexer

import jsonata

# Necessary to support division operations
ExtendedJsonPathLexer.t_SORT_DIRECTION.__doc__ = r",?\s*(//|\\)"


@dataclass
class Sentence:
    """
    Each sentence consists of an attribute name (attr) as well as
    a subject, verb, and (optionally) an object (obj).
    """

    attr: str
    subject: str
    verb: str
    obj: Optional[Any]

    def __iter__(self):
        return iter((self.attr, self.subject, self.verb, self.obj))


@dataclass
class Trigger(Sentence):
    action: Optional[str] = None
    params: Optional[List[str]] = None

    def __iter__(self):
        return iter(
            (self.attr, self.subject, self.verb, self.obj, self.action, self.params)
        )


def jsonpath_parse_val(dict_to_parse, path):
    """
    Parse a path that matches a single scalar value, then return that value.
    """
    jsonpath_expr = parse(path)
    return next(iter(match.value for match in jsonpath_expr.find(dict_to_parse)), None)


def jsonpath_parse_list(dict_to_parse, path):
    """
    Parse a path that matches a list of values, then return that list.
    """
    jsonpath_expr = parse(path)
    return [match.value for match in jsonpath_expr.find(dict_to_parse)]


def parse_jsonata(dict_to_parse, query):
    expr = jsonata.Jsonata(query)
    result = expr.evaluate(dict_to_parse)
    return result


# The functions to call for each verb.
VERB_FUNCTIONS = {
    "parse_jsonata": parse_jsonata,
    "parse": jsonpath_parse_val,
    "parse_list": jsonpath_parse_list,
    ">": lambda x, y: operator.gt(int(x), int(y)),
    "<": lambda x, y: operator.lt(int(x), int(y)),
    "=": lambda x, y: operator.eq(int(x), int(y)),
    "eq": lambda x, y: operator.eq(x, y),
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
    "parse_median": lambda x, y: median(jsonpath_parse_list(x, y)),
    "list_divide": lambda x, y: [float(a) / float(b) for a, b in zip(x, y)],
    "within_last_days": lambda x, y: [
        item for item in x if date.today() - item <= timedelta(days=y)
    ],
}

# A subset of verbs require evaluation of both the
# subject and object before the verb function can run.
JOINING_VERBS = [
    "and",
    "or",
    "list_divide",
]



class DeriveAttributes:
    """
    The DeriveAttributes class accepts a JSON-like source object
    and derives new attributes from that data, based on attribute
    definitions in a list of Sentences.
    """

    def __init__(self, sentences: List[Sentence], source: dict):
        self.sentences = sentences
        self.source = source
        self.evaluated = {}

    def derive(self) -> dict:
        """
        Given a list of sentences and a JSON-like source object,
        compute the derived attributes.
        """
        self.evaluate_attributes()

        # Remove private attributes from result
        result = {k: v for k, v in self.evaluated.items() if k[0] != "_"}

        # Return the list of derived attributes
        return result

    def evaluate_attributes(self) -> dict:
        """
        For every sentence, evaluate it and add the value to
        the evaluated context.
        """
        for sentence in self.sentences:
            if sentence.attr not in self.evaluated:
                self.evaluate_attribute(sentence)

    def get_sentence(self, attr):
        return next(iter(a for a in self.sentences if a.attr == attr), None)

    def evaluate_attribute(self, sentence):
        """
        For the supplied sentence, recursively evaluate the subject
        (if necessary), look up the associated verb function, recursively
        evaluate the object (if necessary), then complete the evaluation
        of the sentence.
        """
        _, subject, verb, obj, *_ = sentence

        # Set the subject, evaluating if necessary
        if subject == "source":
            subject = self.source
        else:
            subject = self.evaluated.get(
                subject, self.evaluate_attribute(self.get_sentence(subject))
            )

        # Get the function that corresponds to the specified verb
        verb_func = VERB_FUNCTIONS[verb]

        # Depending on the verb, some objects may require evaluation
        if verb in JOINING_VERBS:
            obj = self.evaluated.get(
                obj, self.evaluate_attribute(self.get_sentence(obj))
            )

        self.evaluate_sentence(sentence, subject, verb_func, obj)

    def evaluate_sentence(self, sentence, subject, verb_func, obj):
        # Evaluate the sentence by invoking the verb function
        self.evaluated[sentence.attr] = verb_func(subject, obj)


class DeriveRules(DeriveAttributes):
    """
    The DeriveRules class is similar to DeriveAttributes,
    but it treats Sentences that generate boolean values
    as rules.  By only returning the derived True/False rules,
    this class enables a lightweight, flexible rules engine
    that can be evaluated using any() or all().
    """

    def derive(self) -> dict:
        self.evaluate_attributes()

        # Remove private attributes from result
        result = {k: v for k, v in self.evaluated.items() if k[0] != "_"}

        # Return only boolean values
        return [v for v in result.values() if type(v) is bool]


class DeriveTriggers(DeriveAttributes):
    """
    The DeriveTriggers class is similar to DeriveAttributes
    but accepts an additional event_handler function that will
    be used to handle events triggered during the evaluation
    process.  This class accepts Triggers, which are Sentences
    augmented with event-handling attributes.  When a Trigger
    to True, the event_handler function will be invoked with
    two parameters: an action name and a list of parameters,
    which can included derived attributes.
    """

    def __init__(
        self,
        sentences: List[Trigger],
        source: dict,
        event_handler: Callable
    ):
        self.sentences = sentences
        self.source = source
        self.event_handler = event_handler
        self.evaluated = {}

    def evaluate_sentence(self, sentence, subject, verb_func, obj):
        result = verb_func(subject, obj)
        self.evaluated[sentence.attr] = result

        params = (
            [self.evaluated[param] for param in sentence.params]
            if sentence.params
            else []
        )

        if type(result) is bool and result is True and sentence.action:
            self.event_handler(sentence.action, *params)
