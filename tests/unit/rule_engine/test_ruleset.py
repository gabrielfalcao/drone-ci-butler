import re
import unittest
from typing import List
from drone_ci_butler.drone_api.models import (
    Build,
    Step,
    Stage,
    AnalysisContext,
    Output,
    OutputLine,
)
from drone_ci_butler.drone_api.models import AnalysisContext
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


def test_apply_rule_required_conditions_abrupt_interruption():
    "Rule(action=RuleAction.ABRUPT_INTERRUPTION).apply() when failed should not return failed matches"

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=["yarn install"],
    )

    ruleset = RuleSet(
        name="my-ruleset",
        default_action=RuleAction.ABRUPT_INTERRUPTION,
        required_conditions=[
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
                required=True,
            ),
            Condition(
                context_element="step",
                target_attribute="output.lines",
                contains_string="yarn install",
                required=True,
            ),
        ],
    )

    matches = ruleset.apply(context)
    matches.should.have.length_of(1)
    assert (
        "\n".join([t.to_description() for t in matches])
        == r"""
Matched Rule **my-ruleset.required_conditions**:
  Matched Condition: Expect step.name `node_modules` to have exact value `node_modules`
  **Invalid Conditions**:
    Condition could not be fulfilled: Condition: Expect step.exit_code to have exact value `0`
    Condition(context_element='step', target_attribute=<ValueList: ['output.lines']>, matches_regex=None, matches_value=None, value_exact=(), contains_string=<ValueList: ['yarn install']>, is_not=(), value=None, regex_options=<RegexFlag.UNICODE|DOTALL|MULTILINE|IGNORECASE: 58>, required=True) could not find attribute output.lines in step: 'output.lines'
""".strip()
    )


def test_apply_rule_required_conditions_skip_analysis():
    "Rule(action=RuleAction.SKIP_ANALYSIS).apply() when failed should not return failed matches"

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=["yarn install"],
    )

    ruleset = RuleSet(
        name="my-ruleset",
        default_action=RuleAction.SKIP_ANALYSIS,
        required_conditions=[
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
                required=True,
            ),
            Condition(
                context_element="step",
                target_attribute="output.lines",
                contains_string="yarn install",
                required=True,
            ),
        ],
    )

    matches = ruleset.apply(context)
    matches.should.be.empty


def test_apply_rule_required_conditions_request_cancelation():
    "Rule(action=RuleAction.REQUEST_CANCELATION).apply() when failed should not return failed matches"

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        exit_code=0,
        lines=["yarn install"],
    )

    ruleset = RuleSet(
        name="my-ruleset",
        default_action=RuleAction.REQUEST_CANCELATION,
        required_conditions=[
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
                required=True,
            ),
            Condition(
                context_element="step",
                target_attribute="output.lines",
                contains_string="foo bar",
                required=True,
            ),
        ],
    )

    matches = ruleset.apply(context)
    matches.should.have.length_of(1)
    assert (
        "\n".join([t.to_description() for t in matches])
        == r"""
Matched Rule **my-ruleset.required_conditions**:
  Matched Condition: Expect step.name `node_modules` to have exact value `node_modules`
  **Invalid Conditions**:
    Condition could not be fulfilled: Condition: Expect step.exit_code to have exact value `0`
    Condition(context_element='step', target_attribute=<ValueList: ['output.lines']>, matches_regex=None, matches_value=None, value_exact=(), contains_string=<ValueList: ['foo bar']>, is_not=(), value=None, regex_options=<RegexFlag.UNICODE|DOTALL|MULTILINE|IGNORECASE: 58>, required=True) could not find attribute output.lines in step: 'output.lines'
    Cancelation requested on <AnalysisContext build='https://drone.dv.nyt.net/nytm/wf-project-vi/138785'>
""".strip()
    )
