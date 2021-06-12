import re


def test_rule_output_contains_string():
    # Given a rule to match an output containing a string
    rule = Rule(
        output_contains="prettier:docs",
    )

    rule.action.should.equal(RuleAction.NEXT_STEP)


def test_rule_matching_regex_output():
    # Given a rule to match an output by regex
    rule = Rule(
        output_matches_regex=re.compile(f"a DNS-1123 label must consist of lower case"),
    )
    rule.action.should.equal(RuleAction.NEXT_STEP)


def test_rule_action_next_step():
    rule = Rule(
        output_matches_regex=re.compile(f"prettier:docs"), action=RuleAction.NEXT_STEP
    )
    rule.action.should.equal(RuleAction.NEXT_STEP)


def test_rule_action_next_stage():
    rule = Rule(
        output_matches_regex=re.compile(f"prettier:docs"), action=RuleAction.NEXT_STAGE
    )
    rule.action.should.equal(RuleAction.NEXT_STAGE)


def test_rule_action_interrupt_build():
    rule = Rule(
        output_matches_regex=re.compile(f"prettier:docs"),
        action=RuleAction.INTERRUPT_BUILD,
    )
    rule.action.should.equal(RuleAction.INTERRUPT_BUILD)


def test_rule_set_match_single_match():
    # Given a set of rules with only one match

    rule_set = RuleSet(
        [
            Rule(
                output_matches_regex=re.compile(f"prettier:docs"),
                action=RuleAction.INTERRUPT_BUILD,
            ),
            Rule(
                output_matches_regex=re.compile(
                    f"a DNS-1123 label must consist of lower case"
                ),
                action=RuleAction.INTERRUPT_BUILD,
            ),
        ]
    )
