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


def test_apply_rule_omit_failed():
    "Rule(action=RuleAction.OMIT_FAILED).apply() when failed should not return failed matches"

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=[
            '''Couldn't find any versions for "react" that matches "2021"''',
        ],
    )

    ruleset = RuleSet(
        name="my-ruleset",
        rules=[
            Rule(
                name="Step Succeeded",
                conditions=[
                    Condition(
                        context_element="step",
                        target_attribute="exit_code",
                        value_exact=0,
                        required=True,
                    )
                ],
                action=RuleAction.OMIT_FAILED,
            )
        ],
    )

    matches = ruleset.apply(context)
    matches.should.be.empty


def test_apply_rule_default_conditions_required():
    "Rule(action=RuleAction.OMIT_FAILED).apply() when failed should not return failed matches"

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=["yarn install"],
    )

    ruleset = RuleSet(
        name="my-ruleset",
        default_action=RuleAction.ABRUPT_INTERRUPTION,
        default_conditions=[
            Condition(
                context_element="step",
                target_attribute="exit_code",
                value_exact=0,
                required=True,
            ),
            Condition(
                context_element="step",
                target_attribute="name",
                value_exact="node_modules",
                required=False,
            ),
            Condition(
                context_element="step",
                target_attribute="output.lines",
                contains_string="yarn install",
                required=False,
            ),
        ],
    )

    matches = ruleset.apply(context)
    matches.should.have.length_of(1)
