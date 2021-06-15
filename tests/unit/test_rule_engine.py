import re
import unittest
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
    MatchedCondition,
    MatchedRule,
)
from drone_ci_butler.rule_engine.default_rules import wf_project_vi
from .fakes import fake_context_with_output_lines


def test_rule_output_contains_string():
    # Given a rule to match an output containing a string
    rule = Rule(
        name="ValidateDocsPrettified",
        conditions=[
            Condition(
                context_element="step",
                target_attribute=["output", "lines"],
                matches_regex="prettier:docs",
            ),
        ],
        action=RuleAction.NEXT_STEP,
    )
    rule.action.should.equal(RuleAction.NEXT_STEP)


def test_rule_set_match_build():
    # Given a set of rules with only one match
    rule_set = wf_project_vi

    # And a fake context that matches that ruleset
    fake_context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=[
            '''Couldn't find any versions for "react" that matches "2021"''',
        ],
    )
    fake_build = fake_context.build
    fake_stage = fake_context.stage
    fake_step = fake_context.step

    # When I apply the rule set
    matched_rules = rule_set.apply(fake_context)

    # matched_rules.should.be.a(MatchedRule.List)
    matched_rules.should.have.length_of(1)

    descriptions = "\n".join([matched.to_description() for matched in matched_rules])
    assert (
        descriptions
        == r"""
Matched Rule **YarnDependencyNotResolved**:
  Matched Condition: Expect step.exit_code `1` to not be `0`
  Matched Condition: Expect build.link `https://drone.dv.nyt.net/nytm/wf-project-vi/138785` to contain string `nytm/wf-project-vi`
  Matched Condition: Expect step.status `failure` to match value `['fail*', 'running']`
  Matched Condition: Expect step.name `node_modules` to match value `node_modules`
  Matched Condition: Expect step.output.lines `[{'time': 0, 'pos': 0, 'out': 'Couldn\'t find any versions for "react" that matches "2021"'}]` to match regular expression `Couldn't find any versions for\s*(\"([^\"]+)\" that matches \"([^\"]+)\")?`
""".strip()
    )


def test_rule_set_match_build():
    # Given a set of rules with only one match
    rule_set = wf_project_vi

    # And a fake context that matches that ruleset
    fake_context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        step_name="node_modules",
        lines=[
            '''Couldn't find any versions for "react" that matches "2021"''',
        ],
    )

    # When I apply the rule set
    matched_rules = rule_set.apply(fake_context)

    # matched_rules.should.be.a(MatchedRule.List)
    matched_rules.should.have.length_of(1)

    descriptions = "\n".join([matched.to_description() for matched in matched_rules])
    assert (
        descriptions
        == r"""
Matched Rule **YarnDependencyNotResolved**:
  Matched Condition: Expect step.exit_code `1` to not be `0`
  Matched Condition: Expect build.link `https://drone.dv.nyt.net/nytm/wf-project-vi/138785` to contain string `nytm/wf-project-vi`
  Matched Condition: Expect step.status `failure` to match value `['fail*', 'running']`
  Matched Condition: Expect step.name `node_modules` to match value `node_modules`
  Matched Condition: Expect step.output.lines `[{'time': 0, 'pos': 0, 'out': 'Couldn\'t find any versions for "react" that matches "2021"'}]` to match regular expression `Couldn't find any versions for\s*(\"([^\"]+)\" that matches \"([^\"]+)\")?`
""".strip()
    )
