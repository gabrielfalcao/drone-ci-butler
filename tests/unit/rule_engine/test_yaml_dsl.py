from drone_ci_butler.rule_engine.models import (
    Condition,
    ConditionSet,
    MatchedRule,
    Rule,
    ValueList,
    list_of_strings,
)


# default-conditions:
#   - build.link:
#       contains_string: "nytm/wf-project-vi"
#   - step.status: failed
#   - step.exit_code:
#       is_not:  0

# default_action: NEXT_RULE # default to continue analysis onto next step after matching a rule
# default_notify:
#   - slack

# rules:
#   - name: ValidateDocsPrettified
#     when:
#       - step.output:
#           matches_regex: "prettier:docs"
#     action: NEXT_RULE

#   - name: SlackServerError
#     when:
#       - step.name:
#           contains_string: "slack"
#       - step.output:
#           contains_string: "server error"
#     action: NEXT_RULE

#   # skip build (and cancel it if still running)
#   - name: GitBranchNameInvalidForGKEDeploy
#     when:
#       - step.output:
#           matches_regex: "prettier:docs"
#     action: SKIP_ANALYSIS

#   - name: GitMergeConflict
#     when:
#       - step.output:
#           matches_regex: "(not something we can merge|Automatic merge failed; fix conflicts)"

#     action: SKIP_ANALYSIS

#   - name: SamizdatConnectionError
#     when:
#       - step.output:
#           contains_string:
#             - "ECONNREFUSED"
#             - "samizdat"
#     action: SKIP_ANALYSIS
#     notify:
#       - slack
#       - github

#   - name: YarnDependencyNotResolved
#     when:
#       - step.name:
#           contains_string: "node_modules"
#       - step.output:
#           contains_string: "Couldn't find any versions for"

#     action: SKIP_ANALYSIS
#     notify:
#       - slack
#       - github


def test_condition_contains_string_single_string():
    "Condition(contains_string) config serialization with a single string"

    # default-conditions:
    #   - build.link:
    #       contains_string: "nytm/wf-project-vi"

    cond = Condition.from_config(
        {
            "build.link": {
                "contains_string": "nytm/wf-project-vi",
            }
        }
    )

    cond.context_element.should.equal("build")
    cond.target_attribute.should.equal(["link"])
    cond.contains_string.should.equal(ValueList(["nytm/wf-project-vi"]))


def test_condition_contains_string_list_of_strings():
    "Condition(contains_string) config serialization with a list of strings"
    #   - name: SamizdatConnectionError
    #     when:
    #       - step.output:
    #           contains_string:
    #             - "ECONNREFUSED"
    #             - "samizdat"

    cond = Condition.from_config(
        {
            "step.output": {
                "contains_string": ["ECONNREFUSED", "samizdat"],
            }
        }
    )

    cond.context_element.should.equal("step")
    cond.target_attribute.should.equal(["output"])
    cond.contains_string.should.equal(ValueList(["ECONNREFUSED", "samizdat"]))
