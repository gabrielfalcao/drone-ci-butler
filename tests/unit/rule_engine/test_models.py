from drone_ci_butler.rule_engine.models import (
    Condition,
    ConditionSet,
    MatchedRule,
    Rule,
    ValueList,
    list_of_strings,
)
from drone_ci_butler.rule_engine.exceptions import (
    InvalidCondition,
    InvalidConditionSet,
    ConditionRequired,
)
from .fakes import fake_context_with_output_lines


def test_list_of_strings_bytes():
    "list_of_strings() with bytes"

    assert list_of_strings(b"1337") == ["1337"]
    assert list_of_strings([b"foobar"]) == ["foobar"]

    assert list_of_strings(42) == ["42"]
    assert list_of_strings([1337, ["foo"]]) == ["1337", "foo"]


def test_value_list_with_list_of_strings():
    value = ValueList(["build", "link"])

    value.name.should.equal("build.link")
    repr(value).should.equal("<ValueList: ['build', 'link']>")
    value.contains("link").should.equal("link")
    value.contains("*").should.equal("build")
    value.name.should.equal("build.link")
    value.lines.should.equal("build\nlink")


def test_condition_without_context_element():
    "Condition(context_element=None) should raise InvalidCondition"

    when_called = Condition.when.called_with(context_element="")
    when_called.should.have.raised(
        InvalidCondition, "missing context_element from condition"
    )


def test_condition_without_target_attribute():
    "Condition(target_attribute=None) should raise InvalidCondition"

    when_called = Condition.when.called_with(
        context_element="step", target_attribute=[]
    )
    when_called.should.have.raised(
        InvalidCondition, "missing target_attribute from condition"
    )


def test_condition_without_declaring_matchers():
    "Condition() without matchers should raise InvalidCondition"

    when_called = Condition.when.called_with(
        context_element="step", target_attribute=["build", "link"]
    )
    when_called.should.have.raised(
        InvalidCondition,
        "Invalid Condition: Expect step.build.link : does not declare any matchers",
    )


def test_condition_invalid_context_element():
    "Condition(context_element='foobar') should raise InvalidCondition"

    when_called = Condition.when.called_with(
        context_element="foobar",
        target_attribute=["build", "link"],
        matches_value="something",
    )
    when_called.should.have.raised(
        InvalidCondition,
        "Invalid Condition: Expect foobar.build.link to match value `something`: foobar is not a valid context element. ('build', 'stage', 'step')",
    )


def test_process_context_traverse_nested():
    "Condition().process_context() should traverse the value"

    cond = Condition(
        context_element="build",
        target_attribute="link",
        contains_string="nytm/wf-project-vi",
    )

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
    )

    result = cond.process_context(context)

    assert len(result) == 5, "process_context() should return a tuple with 5 members"
    element, path, attribute, location, value = result

    element.should.equal(context.build)
    path.should.equal(["link"])
    attribute.should.equal("link")
    location.should.equal("build.link")
    value.should.equal("https://drone.dv.nyt.net/nytm/wf-project-vi/138785")


def test_process_context_traverse_nested_failed():
    "Condition().process_context() raise InvalidCondition if attribute is not found"

    cond = Condition(
        context_element="build",
        target_attribute="invalid_attr",
        contains_string="nytm/wf-project-vi",
    )

    context = fake_context_with_output_lines(
        build_link="https://drone.dv.nyt.net/nytm/wf-project-vi/138785",
    )

    when_called = cond.process_context.when.called_with(context)

    when_called.should.have.raised(
        InvalidCondition,
        "could not find attribute invalid_attr in build: 'invalid_attr'",
    )


def test_apply_condition_with_invalid_regex():
    "Condition().apply() should raise InvalidCondition if regex is invalid"

    cond = Condition(
        context_element="step",
        target_attribute="name",
        matches_regex="())",
    )

    context = fake_context_with_output_lines(
        step_name="some_step_name",
    )

    when_called = cond.apply.when.called_with(context)

    when_called.should.have.raised(
        InvalidCondition,
        "Invalid Condition: Expect step.name to match regular expression `())` regex is INVALID: `unbalanced parenthesis at position 2`",
    )


def test_apply_required_condition_no_matches():
    "Condition(required=True).apply() should raise InvalidCondition when make no matches"

    cond = Condition(
        context_element="step",
        target_attribute="name",
        matches_regex="(.*fail.*)",
        required=True,
    )

    context = fake_context_with_output_lines(
        step_name="success",
    )

    when_called = cond.apply.when.called_with(context)

    when_called.should.have.raised(
        InvalidCondition,
        "Condition could not be fulfilled: Condition: Expect step.name to match regular expression `(.*fail.*)`",
    )


def test_apply_not_required_condition_no_matches():
    "Condition(required=False).apply() should return empty"

    cond = Condition(
        context_element="step",
        target_attribute="name",
        matches_regex="(.*fail.*)",
        required=False,
    )

    context = fake_context_with_output_lines(
        step_name="success",
    )

    result = cond.apply(context)
    result.should.be.a(list)
    result.should.be.empty


def test_condition_set_invalid_type():
    "ConditionSet should raise InvalidConditionSet when given conditions are of invalid type"

    when_called = ConditionSet.when.called_with("invalid")
    when_called.should.have.raised(
        InvalidConditionSet,
        "invalid <class 'str'> should be a list of Condition objects instead",
    )


def test_condition_apply_with_invalid_condition_type():
    "Condition().apply() should raise InvalidConditionSet if one of its members is not a Condition"
    conditions = ConditionSet(
        [
            Condition(
                context_element="step",
                target_attribute="output.lines",
                matches_regex="(.*fail.*)",
                required=True,
            )
        ]
    )
    conditions.should.have.length_of(1)
    assert (
        conditions.to_description()
        == "Condition: Expect step.output.lines to match regular expression `(.*fail.*)`"
    )

    conditions.extend(["a string is not a valid condition type :)"])

    context = fake_context_with_output_lines()

    when_called = conditions.apply.when.called_with(context)
    when_called.should.have.raised(
        InvalidConditionSet,
        "Invalid Condition: 'a string is not a valid condition type :)' from set",
    )


def test_matched_rule_to_description_with_invalid_conditions():
    "MatchedRule().to_description() with invalid conditions"
    condition = Condition(
        context_element="step",
        target_attribute="name",
        matches_regex="(.*fail.*)",
        required=False,
    )

    context = fake_context_with_output_lines()

    matched_rule = MatchedRule(
        matched_conditions=[],
        invalid_conditions=[ConditionRequired(condition=condition, context=context)],
        context=context,
        rule=Rule(
            name="SomeName",
        ),
    )
    repr(matched_rule).should.equal("<MatchedRule 'SomeName'>")
    assert (
        matched_rule.to_description()
        == r"""
Matched Rule **SomeName**:
  **Invalid Conditions**:
    Condition could not be fulfilled: Condition: Expect step.name to match regular expression `(.*fail.*)`
""".strip()
    )
