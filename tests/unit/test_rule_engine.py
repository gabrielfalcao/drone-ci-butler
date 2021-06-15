import re
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
    fake_context = BuildContext(
        build=Build(
            link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
        ),
        stage=Stage(name="build"),
        step=Step(
            name="node_modules",
            output=Output(
                lines=[
                    OutputLine(
                        time=0,
                        pos=0,
                        out="Couldn't find any versions for react@2021",
                    )
                ]
            ),
        ),
    )

    # When I apply the rule set
    result = rule_set.apply(fake_context)

    result.should.be.a(MatchedRule.List)
    len(result).should.equal(1)
