import re
import unittest
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

from drone_ci_butler.rule_engine.default_rules import build_matches_vi_project
from drone_ci_butler.rule_engine.default_rules import step_failed_or_running
from drone_ci_butler.rule_engine.default_rules import step_exit_code_nonzero


def test_matching_build_property():
    "Condition matching build.link contains_string"
    # Given fake context that matches that condition
    context_build_link = AnalysisContext(
        build=Build(
            link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        )
    )

    assert (
        build_matches_vi_project.describe_matches()
        == "to contain string `nytm/wf-project-vi`"
    )
    # When I apply a condition that matches the build
    matched_conditions = build_matches_vi_project.apply(context_build_link)

    # Then it should have 1 match
    matched_conditions.should.have.length_of(1)

    matched_conditions[0].to_description().should.equal(
        "Matched Condition: Expect build.link `https://drone.dv.nyt.net/nytm/wf-project-vi/138785` to contain string `nytm/wf-project-vi`"
    )


def test_matching_step_property_matches_value_list():
    "Condition matching step.status matches_value"
    # Given fake context that matches that condition
    context_step_failure = AnalysisContext(
        step=Step(
            status="failure",
        )
    )
    context_step_running = AnalysisContext(
        step=Step(
            status="running",
        )
    )
    assert (
        step_failed_or_running.describe_matches()
        == "to match value `['fail*', 'running']`"
    )

    # When I apply a condition that matches the step
    matched_conditions_failure = step_failed_or_running.apply(context_step_failure)
    matched_conditions_running = step_failed_or_running.apply(context_step_running)

    matched_conditions_failure.should.have.length_of(1)
    matched_conditions_running.should.have.length_of(1)

    # Then it should have 1 match
    matched_conditions_failure[0].to_description().should.equal(
        "Matched Condition: Expect step.status `failure` to match value `['fail*', 'running']`"
    )
    matched_conditions_running[0].to_description().should.equal(
        "Matched Condition: Expect step.status `running` to match value `['fail*', 'running']`"
    )


def test_matching_step_property_is_not_value():
    "Condition matching step.status is_not 0"
    # Given fake context that matches that condition
    context_step_nonzero = AnalysisContext(step=Step(exit_code=42))

    assert step_exit_code_nonzero.describe_matches() == "to not be `0`"
    # When I apply a condition that matches the step
    matched_conditions = step_exit_code_nonzero.apply(context_step_nonzero)

    matched_conditions.should.have.length_of(1)

    # Then it should have 1 match
    assert matched_conditions[0].to_description() == (
        "Matched Condition: Expect step.exit_code `42` to not be `0`"
    )


def test_matching_step_property_value_exact_value():
    "Condition matching step.status value_exact 0"
    # Given fake context that matches that condition

    success_step = Condition(
        context_element="step",
        target_attribute="exit_code",
        value_exact=0,
        required=True,
    )

    context_step_nonzero = AnalysisContext(step=Step(exit_code=0))

    assert success_step.describe_matches() == "to have exact value `0`"
    # When I apply a condition that matches the step
    matched_conditions = success_step.apply(context_step_nonzero)

    matched_conditions.should.have.length_of(1)

    # Then it should have 1 match
    assert matched_conditions[0].to_description() == (
        "Matched Condition: Expect step.exit_code `0` to have exact value `0`"
    )
