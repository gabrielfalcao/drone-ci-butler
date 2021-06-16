import re
from re import Pattern
from enum import Enum

from typing import Union
from typing import Optional
from typing import Type
from typing import List
from typing import Any
from typing import TypeVar
from typing import Set
from typing import Iterator
from typing import Tuple
from fnmatch import fnmatch

from itertools import chain
from uiclasses import Model, UserFriendlyObject
from uiclasses import ModelList, ModelSet
from uiclasses.typing import Property
from datetime import datetime
from drone_ci_butler.config import Config
from drone_ci_butler.drone_api.models import BuildContext, Build, Step, Stage
from .exceptions import ConditionRequired
from .exceptions import InvalidCondition
from .exceptions import InvalidConditionSet
from .exceptions import NotStringOrListOfStrings


class RuleAction(Enum):
    NEXT_RULE = "NEXT_RULE"
    OMIT_FAILED = "OMIT_FAILED"
    SKIP_ANALYSIS = "SKIP_ANALYSIS"
    REQUEST_CANCELATION = "REQUEST_CANCELATION"
    ABRUPT_INTERRUPTION = "ABRUPT_INTERRUPTION"


class ConditionMatchType(Enum):
    CONTAINS_STRING = "CONTAINS_STRING"
    IS_NOT = "IS_NOT"
    MATCHES_REGEX = "MATCHES_REGEX"
    MATCHES_VALUE = "MATCHES_VALUE"
    VALUE_EXACT = "VALUE_EXACT"


DEFAULT_REGEX_OPTIONS: int = re.I | re.MULTILINE | re.DOTALL | re.UNICODE
DEFAULT_ACTION: RuleAction = RuleAction.NEXT_RULE
T = TypeVar("T")
nothing = type("nothing", (tuple,), {})()


StringOrListOfStrings = Union[List[str], str]


def list_of_strings(value: StringOrListOfStrings) -> List[str]:
    result = []
    if isinstance(value, str):
        result.append(value)

    elif isinstance(value, bytes):
        result.append(value.decode("utf-8"))

    elif isinstance(value, list):
        result.extend(chain(*list(map(list_of_strings, value))))
    else:
        result.append(str(value))

    return result


class ValueList(list, UserFriendlyObject):
    values: List[str]
    name: str

    def __init__(self, value_or_values: StringOrListOfStrings):
        self.values = list_of_strings(value_or_values)
        super().__init__(self.values)

    def __repr__(self):
        return f"<ValueList: {self.values}>"

    def contains(self, value_or_values: StringOrListOfStrings) -> Optional[bool]:
        for theirs in list_of_strings(value_or_values):
            for mine in self.values:
                if fnmatch(f"{theirs}", f"{mine}") or fnmatch(f"{mine}", f"{theirs}"):
                    return mine
                if theirs in mine or mine in theirs:
                    return mine

    @property
    def name(self) -> str:
        return ".".join(self.values)

    @property
    def lines(self) -> str:
        return "\n".join(self.values)


class Condition(Model):
    __id_attributes__ = [
        "context_element",
        "target_attribute",
        "matches_regex",
        "matches_value",
        "contains_string",
        "is_not",
        "value_exact",
        "required",
    ]
    context_element: str
    target_attribute: ValueList
    matches_regex: Union[str, Pattern]
    matches_value: Any
    value_exact: Any
    contains_string: ValueList
    is_not: Any
    value: Any
    regex_options: int
    required: bool

    def __init__(
        self,
        condition=None,
        **kw,
    ):
        if isinstance(condition, dict):
            kw.update(condition)
        elif isinstance(condition, Condition):
            kw["required"] = condition.required
            kw["is_not"] = condition.is_not
            kw["target_attribute"] = condition.target_attribute
            kw["contains_string"] = condition.contains_string
            kw["context_element"] = condition.context_element
            kw["matches_regex"] = condition.matches_regex
            kw["matches_value"] = condition.matches_value
            kw["value_exact"] = condition.value_exact
            kw["value"] = condition.value

        elif condition is not None:  # pragma: no cover
            raise RuntimeError(f"invalid condition {repr(condition)}")

        for attr in ("target_attribute", "contains_string"):
            if attr in kw:
                val = kw[attr] or []
                kw[attr] = ValueList(val)

        if not kw.get("regex_options"):
            kw["regex_options"] = DEFAULT_REGEX_OPTIONS

        if "is_not" not in kw:
            kw["is_not"] = nothing

        if "value_exact" not in kw:
            kw["value_exact"] = nothing

        if "required" not in kw:
            kw["required"] = True

        super().__init__(**kw)

        if not self.context_element:
            raise InvalidCondition(
                f"missing context_element from condition {self}",
                condition=self,
            )

        if not self.target_attribute.name:
            raise InvalidCondition(
                f"missing target_attribute from condition {self}",
                condition=self,
            )

        if not self.describe_matches():
            raise InvalidCondition(
                f"Invalid {self.to_description()}: does not declare any matchers",
                condition=self,
            )
        valid_elements = ("build", "stage", "step")
        if self.context_element not in valid_elements:
            raise InvalidCondition(
                f"Invalid {self.to_description()}: {self.context_element} is not a valid context element. {valid_elements}",
                condition=self,
            )

    def to_description(self):
        match = self.describe_matches()
        return f"Condition: Expect {self.context_element}.{self.target_attribute.name} {match}"

    def describe_matches(self) -> List[str]:
        message = []
        if self.contains_string:
            message.append(f"to contain string `{self.contains_string.name}`")

        if self.matches_regex:
            message.append(f"to match regular expression `{self.matches_regex}`")

        if self.matches_value:
            message.append(f"to match value `{self.matches_value}`")

        if not isinstance(self.is_not, tuple):
            message.append(f"to not be `{self.is_not}`")

        if not isinstance(self.value_exact, tuple):
            message.append(f"to have exact value `{self.value_exact}`")
        # else:
        #     # TODO: unit test

        return ", ".join(message)

    def process_context(
        self: Type[T], context: BuildContext
    ) -> Tuple[Any, List[str], str, str, Any]:
        element = context[self.context_element]

        path = list_of_strings(self.target_attribute)
        attribute = ".".join(path)
        location = f"{self.context_element}.{attribute}"
        value = element
        for attr in path:
            try:
                value = getattr(value, attr, nothing)
                if value is nothing:
                    raise KeyError(attr)

            except (AttributeError, KeyError) as e:
                raise InvalidCondition(
                    f"{self} could not find attribute {attribute} in {self.context_element}: {e}",
                    condition=self,
                    context=context,
                )

        return element, path, attribute, location, value

    def apply(self: Type[T], context: BuildContext) -> List[T]:
        result = []
        element, path, attribute, location, value = self.process_context(context)

        def matched_condition_of_type(match_type: ConditionMatchType, **kw):
            if not kw.get("value"):
                kw["value"] = value
            return MatchedCondition(
                condition=self,
                context=context,
                element=element,
                attribute=attribute,
                location=location,
                match_type=match_type,
                **kw,
            )

        if self.contains_string:
            contains_string = self.contains_string.contains(value)
            if contains_string:
                result.append(
                    matched_condition_of_type(
                        ConditionMatchType.CONTAINS_STRING,
                    )
                )

        if self.matches_regex:
            try:
                regex = re.compile(self.matches_regex, self.regex_options)
            except re.error as e:
                raise InvalidCondition(
                    f"Invalid {self.to_description()} regex is INVALID: `{e}`",
                    condition=self,
                    context=context,
                )

            found = regex.search(str(value))
            if found:
                result.append(
                    matched_condition_of_type(
                        ConditionMatchType.MATCHES_REGEX,
                        value=value,
                    )
                )
                # TODO: unit test

        if self.matches_value:
            # match lists
            if isinstance(self.matches_value, list):
                # TODO: use fnmatch
                fnmatch
                matched = any(
                    [fnmatch(value, pattern) for pattern in self.matches_value]
                )
                if matched:
                    result.append(
                        matched_condition_of_type(
                            ConditionMatchType.MATCHES_VALUE,
                        )
                    )
            # match literal values
            else:
                matched = value == self.matches_value
                if matched:
                    result.append(
                        matched_condition_of_type(
                            ConditionMatchType.MATCHES_VALUE,
                        )
                    )
        if not isinstance(self.is_not, tuple):
            matched = value != self.is_not
            if matched:
                result.append(
                    matched_condition_of_type(
                        ConditionMatchType.IS_NOT,
                    )
                )

        if not isinstance(self.value_exact, tuple):
            matched = value == self.value_exact
            if matched:
                result.append(
                    matched_condition_of_type(
                        ConditionMatchType.VALUE_EXACT,
                    )
                )

        if self.required and len(result) == 0:
            raise ConditionRequired(
                condition=self,
                context=context,
            )
        # TODO: implement other types of match here 😉
        return result


class MatchedCondition(Model):
    __id_attributes__ = ["condition", "location", "value", "match_type"]
    condition: Condition
    context: BuildContext
    value: Any
    element: Union[Build, Stage, Step]
    attribute: str
    location: str
    match_type: ConditionMatchType
    matched_regex_groups: List[str]

    def to_description(self):
        matches = self.condition.describe_matches()
        # if not matches:
        #     import ipdb;ipdb.set_trace()  # fmt: skip
        return f"Matched Condition: Expect {self.condition.context_element}.{self.attribute} `{self.value}` {matches}"


class ConditionSet(Model):
    conditions: Condition.Set

    def __init__(
        self,
        conditions: Condition.List = None,
        **kw,
    ):
        if isinstance(conditions, ConditionSet):
            kw["conditions"] = Condition.Set(conditions.conditions)
        elif isinstance(conditions, (list, set, ModelList, ModelSet)):
            kw["conditions"] = Condition.Set(map(Condition, conditions))
        elif isinstance(conditions, (dict)):
            kw["conditions"] = Condition.Set(map(Condition, conditions["conditions"]))
        else:
            raise InvalidConditionSet(
                f"{conditions} {type(conditions)} should be a list of Condition objects instead"
            )

        super().__init__(**kw)

    def to_description(self) -> str:
        return "\n".join([c.to_description() for c in self.conditions])

    def __iter__(self) -> Iterator[Condition]:
        for condition in self.conditions:
            yield condition

    def __len__(self) -> int:
        return len(self.conditions)

    def apply(
        self,
        context: BuildContext,
    ) -> Tuple[MatchedCondition.List, List[InvalidCondition]]:
        matched_conditions = MatchedCondition.List([])
        invalid_conditions = []
        matched_count = 0
        required_count = 0
        total_conditions = len(self.conditions)
        total_required = len(
            [c for c in self.conditions if getattr(c, "required", False)]
        )
        conditions = list(self.conditions)
        for condition in conditions:
            if not isinstance(condition, Condition):
                raise InvalidConditionSet(
                    f"Invalid Condition: {repr(condition)} from set {conditions}"
                )
            try:
                matched = condition.apply(context)
            except InvalidCondition as e:
                invalid_conditions.append(e)
                continue
            if matched:
                matched_count += 1
                if condition.required:
                    required_count += 1

                matched_conditions.extend(matched)
            elif condition.required:
                invalid_conditions.append(
                    ConditionRequired(condition=condition, context=context)
                )

        did_match_all = matched_count >= total_conditions
        did_match_any = matched_count > 0
        if did_match_all:
            return matched_conditions, invalid_conditions
        elif did_match_any:
            return matched_conditions, invalid_conditions
        else:
            return [], invalid_conditions

    def extend(self: Type[T], conditions: Condition.List) -> T:
        for c in conditions:
            self.conditions.add(c)

        return self


class Rule(Model):
    __id_attributes__ = ["name", "action"]
    name: str

    action: RuleAction
    notify: ValueList

    conditions: ConditionSet

    def with_preconditions(self: Type[T], pre_conditions: Condition.List) -> T:
        pre_conditions = ConditionSet(pre_conditions or [])
        pre_conditions.extend(self.conditions or [])
        self.conditions = pre_conditions
        return self

    def with_default_action(self: Type[T], default_action: RuleAction) -> T:
        if not self.action:
            self.action = default_action

        return self

    def apply(
        self, context: BuildContext
    ) -> Tuple[MatchedCondition.List, List[InvalidCondition]]:
        matched_conditions, invalid_conditions = self.conditions.apply(context)
        failed_required_conditions = [
            c for c in invalid_conditions if isinstance(c, ConditionRequired)
        ]
        required_conditions = [c for c in self.conditions if c.required]
        if len(failed_required_conditions) > 0:
            return [], []
        return matched_conditions, invalid_conditions

    def match(self, context: BuildContext):
        matched_conditions, invalid_conditions = self.apply(context)
        return MatchedRule(
            matched_conditions=matched_conditions,
            invalid_conditions=invalid_conditions,
            context=context,
            rule=self,
        )


class MatchedRule(Model):
    __id_attributes__ = ["rule", "context"]
    matched_conditions: MatchedCondition.List
    invalid_conditions: List[InvalidCondition]
    context: BuildContext
    rule: Rule

    def __repr__(self):
        return f"<MatchedRule {repr(self.rule.name)}>"

    def to_description(self, indent=2):
        padding = " " * indent
        message = [f"Matched Rule **{self.rule.name}**:"]
        for condition in self.matched_conditions or []:
            description = condition.to_description()
            message.append(f"{padding}{description}")

        if self.invalid_conditions or []:
            message.append(f"{padding}**Invalid Conditions**:")

        for condition in self.invalid_conditions or []:
            message.append(f"{padding * 2}{condition}")

        return "\n".join(message)


class RuleSet(Model):

    name: str
    default_conditions: ConditionSet
    required_conditions: ConditionSet
    default_action: RuleAction
    default_notify: StringOrListOfStrings
    rules: Rule.List

    # @classmethod
    # def from_config(cls: Type[T], config: Config) -> T:
    #     data = config.load_drone_output_rules()
    #     return cls(**data)

    def apply(self, context: BuildContext) -> MatchedRule.List:
        required_conditions = self.required_conditions or []
        if required_conditions:
            required_matches, invalid_conditions = required_conditions.apply(context)
        else:
            required_matches = invalid_conditions = []
        invalid_matches = [
            c.condition
            for c in filter(
                lambda x: isinstance(x, ConditionRequired), invalid_conditions
            )
        ]

        matched_rules = MatchedRule.List([])

        if len(invalid_conditions) == len(required_conditions):
            if self.default_action is None or self.default_action in (RuleAction.OMIT_FAILED, RuleAction.NEXT_RULE):
                pass
            elif self.default_action == RuleAction.SKIP_ANALYSIS:
                return matched_rules
            elif self.default_action == RuleAction.ABRUPT_INTERRUPTION:
                matched_rules.append(
                    MatchedRule(
                        rule=Rule(
                            name=f"{self.name}.default_action",
                            conditions=required_conditions,
                            action=self.default_action,
                        ),
                        matched_conditions=required_conditions,
                        invalid_conditions=invalid_conditions,
                        context=context,
                    )
                )
                return matched_rules
            else:
                import ipdb;ipdb.set_trace()  # fmt: skip

        elif required_matches:
            # just proceed to apply rules
            pass

        for rule in self.rules or []:
            rule = (
                rule.with_preconditions(pre_conditions=required_conditions)
                .with_preconditions(
                    pre_conditions=self.default_conditions,
                )
                .with_default_action(self.default_action)
            )

            matched_conditions, invalid_conditions = rule.apply(context)
            if matched_conditions or invalid_conditions:
                if rule.action is None or rule.action != RuleAction.OMIT_FAILED:
                    matched_rules.append(
                        MatchedRule(
                            matched_conditions=matched_conditions,
                            invalid_conditions=invalid_conditions,
                            context=context,
                            rule=rule,
                        )
                    )
                elif rule.action == RuleAction.NEXT_RULE:
                    continue
                elif rule.action == RuleAction.SKIP_ANALYSIS:
                    break
                else:
                    logger.error(f"rule {rule} has invalid action: {rule.action}")

        return matched_rules
