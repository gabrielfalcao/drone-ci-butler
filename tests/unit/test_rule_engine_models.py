from drone_ci_butler.rule_engine.models import list_of_strings, ValueList, Condition
from drone_ci_butler.rule_engine.exceptions import InvalidCondition
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
        required=True,
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
