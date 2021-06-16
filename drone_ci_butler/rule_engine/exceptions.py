"""Exception messages contain valid markdown because so they
can be posted to slack or github if the user opts in the feature
"""


from typing import List, Union, Any, Optional
from drone_ci_butler.drone_api.models import BuildContext


class InvalidCondition(Exception):
    def __init__(self, message, condition: Any, context: Optional[BuildContext] = None):
        self.message = message
        self.condition = condition
        self.context = context
        super().__init__(f"{message}")


class ConditionRequired(InvalidCondition):
    """specifically raised when a condition with required=True does not match"""

    def __init__(self, condition: Any, context: BuildContext):
        description = condition.to_description()
        message = f"Condition could not be fulfilled: {description}"
        super().__init__(message, condition, context)


class CancelationRequested(InvalidCondition):
    """specifically raised when a rule or ruleset have the RuleAction.REQUEST_CANCELATION"""

    def __init__(self, context: BuildContext):
        message = f"Cancelation requested on {context}"
        super().__init__(message, None, context)


class InvalidConditionSet(Exception):
    def __init__(self, message):
        super().__init__(f"{message}")


class NotStringOrListOfStrings(Exception):
    def __init__(self, v: Union[List[str], str]):
        super().__init__(f"got invalid value {v} {type(v)}")
