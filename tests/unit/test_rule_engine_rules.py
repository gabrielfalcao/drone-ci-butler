import re
import unittest
from typing import List
from drone_ci_butler.drone_api.models import (
    Build,
    Step,
    Stage,
    BuildContext,
    Output,
    OutputLine,
)
from drone_ci_butler.drone_api.models import BuildContext
from drone_ci_butler.rule_engine.models import (
    Rule,
    RuleAction,
    Condition,
    RuleSet,
    ConditionSet,
    MatchedCondition,
    MatchedRule,
)
from drone_ci_butler.rule_engine.default_rules import GitBranchNameInvalidForGKEDeploy
from drone_ci_butler.rule_engine.default_rules import GitMergeConflict
from drone_ci_butler.rule_engine.default_rules import SamizdatConnectionError
from drone_ci_butler.rule_engine.default_rules import SlackServerError
from drone_ci_butler.rule_engine.default_rules import ValidateDocsPrettified
from drone_ci_butler.rule_engine.default_rules import YarnDependencyNotResolved
from .fakes import fake_context_with_output_lines


def test_rule_matches_value_and_matches_regex():
    "Rule with all conditions: matches_value and matches_regex"

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=[
            '''Couldn't find any versions for "react" that matches "2021"''',
        ],
    )

    matched_rule = YarnDependencyNotResolved.match(context)
    repr(matched_rule).should.equal("<MatchedRule 'YarnDependencyNotResolved'>")
    matched_rule.to_description().should.equal(
        "Matched Rule **YarnDependencyNotResolved**:\n  Matched Condition: Expect step.name `node_modules` to match value `node_modules`\n  Matched Condition: Expect step.output.lines `[{'time': 0, 'pos': 0, 'out': 'Couldn\\'t find any versions for \"react\" that matches \"2021\"'}]` to match regular expression `Couldn't find any versions for\\s*(\\\"([^\\\"]+)\\\" that matches \\\"([^\\\"]+)\\\")?`"
    )
    matched_conditions, invalid_conditions = YarnDependencyNotResolved.apply(context)

    matched_conditions.should.have.length_of(2)
    invalid_conditions.should.be.empty

    assert (
        "\n".join([c.to_description() for c in matched_conditions])
        == r"""
Matched Condition: Expect step.name `node_modules` to match value `node_modules`
Matched Condition: Expect step.output.lines `Couldn't find any versions for "react" that matches "2021"` to match regular expression `Couldn't find any versions for\s*(\"([^\"]+)\" that matches \"([^\"]+)\")?`
""".strip()
    )
