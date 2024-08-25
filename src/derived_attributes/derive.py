import csv
from io import StringIO
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

import jsonata
from jsonpath_ng.ext import parse
from pydantic import ValidationError, model_validator
from pydantic.dataclasses import dataclass

from src.derived_attributes.verbs import JOINING_VERBS, JSONPATH_VERBS, VERB_FUNCTIONS

T = TypeVar("T")


@dataclass
class Sentence:
    """
    Each sentence consists of an attribute name (attr) as well as
    a subject, verb, and (optionally) an object (obj).
    """

    attr: str
    subject: str
    verb: str
    obj: Optional[Any] = None

    @model_validator(mode="after")
    def validate_syntax(cls, values):
        if values.verb not in VERB_FUNCTIONS:
            raise ValueError(f"Unsupported verb in sentence: {values.verb}")

        if values.verb == "parse_jsonata":
            try:
                jsonata.Jsonata(values.obj)
            except Exception:
                raise SyntaxError(f"Invalid Jsonata syntax for {values.obj}")

        if values.verb in JSONPATH_VERBS:
            if not values.obj:
                raise ValueError("Required Jsonpath object not present")

            try:
                parse(values.obj)
            except Exception:
                raise SyntaxError(f"Invalid Jsonpath syntax for {values.obj}")

        return values

    def __iter__(self):
        return iter((self.attr, self.subject, self.verb, self.obj))


@dataclass
class Trigger(Sentence):
    action: Optional[str] = None
    params: Optional[List[Any]] = None

    @model_validator(mode="after")
    def validate_syntax(cls, values):
        super().validate_syntax(values)
        if values.params and not values.action:
            raise ValueError("Parameters specified without action.")

    def __iter__(self):
        return iter(
            (self.attr, self.subject, self.verb, self.obj, self.action, self.params)
        )


class InputBuilder:
    """
    Create and validate input objects (such as Sentences
    or Triggers) based on supplied data.
    """

    @staticmethod
    def from_list_of_dicts(data: List[dict], data_type: Type[T] = Sentence) -> List[T]:
        try:

            # If trigger parameters are present, split them
            for item in data:
                if item.get("params") == "":
                    item["params"] = None
                elif item.get("params") and isinstance(item["params"], str):
                    item["params"] = item["params"].split(",")

            return [data_type(**item) for item in data]
        except ValidationError:
            raise

    @staticmethod
    def from_csv(
        csv_data: Union[str, StringIO], data_type: Type[T] = Sentence
    ) -> List[T]:
        # If csv_data is a string, convert it to a StringIO object
        # so csv.reader can read it
        if isinstance(csv_data, str):
            csv_data = StringIO(csv_data)

        # Parse the CSV data into a list of dictionaries
        reader = csv.DictReader(csv_data)

        return InputBuilder.from_list_of_dicts([row for row in reader], data_type)


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
        result = {k: v for k, v in self.evaluated.items() if not k.startswith("_")}

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

    def get_sentence(self, attr: str) -> Optional[Sentence]:
        """
        Get the sentence that matches the supplied attribute name,
        if it exists in self.sentences.
        """
        return next(iter(s for s in self.sentences if s.attr == attr), None)

    def evaluate_attribute(self, sentence: Sentence):
        """
        For the supplied sentence, recursively evaluate the subject
        (if necessary), look up the associated verb function, recursively
        evaluate the object (if necessary), then complete the evaluation
        of the sentence.
        """
        _, subject, verb, obj, *_ = sentence

        # Evaluate the subject
        subject = self.evaluate_subject(subject)

        # Get the function that corresponds to the specified verb
        verb_func = VERB_FUNCTIONS.get(verb)

        # Evaluate the object if the verb requires it
        if verb in JOINING_VERBS:
            obj = self.evaluate_object(obj)

        # Or maybe the object has already been evaluated
        elif self.evaluated.get(obj):
            obj = self.evaluated[obj]

        self.evaluate_sentence(sentence, subject, verb_func, obj)

    def evaluate_subject(self, subject: str):
        """
        Fetch or evaluate the sentence subject.
        """
        if subject == "source":
            return self.source
        return self.evaluated.get(
            subject, self.evaluate_attribute(self.get_sentence(subject))
        )

    def evaluate_object(self, obj: str):
        """
        Fetch or evaluate the sentence object.
        """
        return self.evaluated.get(obj, self.evaluate_attribute(self.get_sentence(obj)))

    def evaluate_sentence(
        self, sentence: Sentence, subject: str, verb_func: Callable, obj: str
    ):
        """
        Evaluate the sentence by invoking the verb function.
        """
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
        result = {k: v for k, v in self.evaluated.items() if not k.startswith("_")}

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

    def __init__(self, sentences: List[Trigger], source: dict, event_handler: Callable):
        self.sentences = sentences
        self.source = source
        self.event_handler = event_handler
        self.evaluated = {}

    def evaluate_sentence(self, sentence, subject, verb_func, obj):
        result = verb_func(subject, obj)
        self.evaluated[sentence.attr] = result

        params = (
            {param: self.evaluated.get(param, param) for param in sentence.params}
            if sentence.params
            else {}
        )

        if type(result) is bool and result is True and sentence.action:
            self.event_handler(sentence.action, **params)
