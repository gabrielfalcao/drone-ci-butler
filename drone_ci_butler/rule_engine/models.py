from re import Pattern
from enum import Enum
from typing import Union, Optional, Type, List, Any, TypeVar, Set
from itertools import chain
from uiclasses import Model, UserFriendlyObject
from uiclasses.typing import Property
from datetime import datetime
from drone_ci_butler.config import Config
from drone_ci_butler.drone_api.models import BuildContext, Build, Step, Stage
from .exceptions import InvalidCondition
from .exceptions import NotStringOrListOfStrings


class RuleAction(Enum):
    NEXT_STEP = "NEXT_STEP"
    NEXT_STAGE = "NEXT_STAGE"
    INTERRUPT_BUILD = "INTERRUPT_BUILD"


DEFAULT_ACTION = RuleAction.NEXT_STEP
T = TypeVar("T")


StringOrListOfStrings = Union[List[str], str]


def list_of_strings(value: StringOrListOfStrings) -> List[str]:
    result = []
    if isinstance(value, str):
        result.append(value)

    elif isinstance(value, bytes):
        value.append(value.decode("utf-8"))

    elif isinstance(value, list):
        result.extend(value)
    else:
        raise NotStringOrListOfStrings(value)

    return result


class ValueList(list, UserFriendlyObject):
    values: List[str]

    def __init__(self, value_or_values: Union[List[str], str]):
        self.values = list_of_strings(value_or_values)
        super().__init__(self.values)

    def __repr__(self):
        return f"<ValueList: {self.values}>"

    def contains(self, value_or_values: StringOrListOfStrings) -> bool:
        for theirs in list_of_strings(value_or_values):
            for mine in self.values:
                if mine in theirs or theirs in mine:
                    return theirs


class Condition(Model):
    context_element: str
    target_attribute: ValueList
    matches_regex: Union[str, Pattern]
    matches_value: Any
    contains_string: ValueList
    value: Any

    def __init__(
        self,
        *args,
        **kw,
    ):
        for attr in ("target_attribute", "contains_string"):
            if attr in kw:
                kw[attr] = ValueList(kw[attr])

        super().__init__(*args, **kw)

        if not self.context_element:
            raise InvalidCondition(f"missing context_element from condition {self}")

    def apply(self: Type[T], context: BuildContext) -> T:
        valid_elements = ("build", "stage", "step")
        if self.context_element not in valid_elements:
            raise InvalidCondition(
                f"{self.context_element} is not a valid context element. {valid_elements} ({self})"
            )

        element = context[self.context_element]

        value = element
        path = list_of_strings(self.target_attribute)
        attribute = ".".join(path)

        for attr in path:
            try:
                value = getattr(value, attr)
            except AttributeError as e:
                raise InvalidCondition(
                    f"{self} could not find attribute {attribute} in {element}: {e}"
                )

        if self.contains_string:
            contains_string = self.contains_string.contains(list_of_strings(value))
            if contains_string:
                return MatchedCondition(
                    condition=self,
                    context=context,
                    value=value,
                    element=element,
                    attribute=attribute,
                )

        if self.matches_regex:
            import ipdb;ipdb.set_trace()  # fmt: skip


class MatchedCondition(Model):
    condition: Condition
    context: BuildContext
    value: Any
    element: Union[Build, Stage, Step]
    attribute: str


class ConditionSet(Model):
    conditions: Condition.Set

    def __init__(
        self,
        conditions: Condition.List = None,
        **kw,
    ):
        if not isinstance(conditions, (dict, Model)):
            kw["conditions"] = conditions

        super().__init__(**kw)

    def apply(self, context: BuildContext) -> MatchedCondition.List:
        matched_conditions = []
        for condition in self.conditions:
            matched = condition.apply(context)
            if matched:
                matched_conditions.append(matched)
        return MatchedCondition.List(matched_conditions)


class Rule(Model):

    name: str
    output_contains: Optional[str]
    output_matches_regex: Optional[Pattern]

    action: RuleAction
    notify: ValueList

    conditions: ConditionSet

    def initialize(self, *args, **kw):
        if not self.action:
            self.action = DEFAULT_ACTION

    def apply(self, context: BuildContext) -> MatchedCondition.List:
        matched_conditions = self.conditions.apply(context)
        if not matched_conditions:
            return

        matched_rules = []
        for matched in self.matched_conditions:
            result = MatchedRule(
                rule=self, matched_conditions=matched_conditions, context=context
            )
            matched_rules.append(result)
            if self.action == RuleAction.INTERRUPT_BUILD:
                break

            elif (
                isinstance(matched.element, Step)
                and self.action == RuleAction.NEXT_STEP
            ):
                continue
            elif (
                isinstance(matched.element, Stage)
                and self.action == RuleAction.NEXT_STAGE
            ):
                continue
            else:
                continue

        return MatchedRule.List(matched_rules)


class MatchedRule(Model):

    matched_conditions: MatchedCondition.List
    context: BuildContext
    rule: Rule


class RuleSet(Model):

    name: str
    default_conditions: ConditionSet
    default_action: RuleAction
    default_notify: StringOrListOfStrings
    rules: Rule.List

    @classmethod
    def from_config(cls: Type[T], config: Config) -> T:
        data = config.load_drone_output_rules()

        return cls(**data)

    def apply(self, context: BuildContext) -> MatchedCondition.List:
        matched_conditions = self.default_conditions.apply(context)
        matched_rules = []
        default_rule = Rule(
            name=f"{self}.default_conditions",
            action=self.default_action,
            notify=ValueList(self.default_notify),
        )

        for matched in matched_conditions:
            matched_rules.append(
                MatchedRule(
                    matched_conditions=matched_conditions,
                    rule=default_rule,
                    context=context,
                )
            )
            if self.default_action in (RuleAction.NEXT_STEP, RuleAction.NEXT_STAGE):
                continue
            elif self.default_action == RuleAction.INTERRUPT_BUILD:
                break

        return MatchedRule.List(matched_rules)
