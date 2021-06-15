from .models import Rule, Condition, RuleAction, RuleSet


ValidateDocsPrettified = Rule(
    name="ValidateDocsPrettified",
    conditions=[
        Condition(
            context_element="step",
            target_attribute=["output", "lines"],
            matches_regex="prettier:docs",
            possible_problem="changed docs without following our formatting style.",
            possible_solution="run `yarn prettier:docs` to fix the issue",
        ),
    ],
    action=RuleAction.NEXT_STEP,
)

SlackServerError = Rule(
    name="SlackServerError",
    conditions=[
        Condition(
            context_element="step", target_attribute="name", contains_string="slack"
        ),
        Condition(
            context_element="step",
            target_attribute=["output", "lines"],
            contains_string="server error",
        ),
    ],
    action=RuleAction.NEXT_STEP,
)

GitBranchNameInvalidForGKEDeploy = Rule(
    name="GitBranchNameInvalidForGKEDeploy",
    conditions=[
        Condition(
            context_element="step",
            target_attribute=["output", "lines"],
            matches_regex="a DNS-1123 label must consist of lower case",
            possible_problem="your branch name is invalid: {build.ref}",
            possible_solution="\n".join(
                [
                    "1. Create a new branch off of {build.ref}, e.g.:",
                    "`git checkout {build.ref} && git co -b new-name-properly-formatted`",
                    "",
                    "2. Delete this invalid branch locally",
                    "`git branch -D {build.ref}",
                    "",
                    "3. Delete this invalid branch remotely",
                    "`git push origin :{build.ref}",
                ]
            ),
        ),
    ],
    action=RuleAction.INTERRUPT_BUILD,
)

SamizdatConnectionError = Rule(
    name="SamizdatConnectionError",
    conditions=[
        Condition(
            context_element="step",
            target_attribute=["output", "lines"],
            contains_string=["ECONNREFUSED", "samizdat"],
        ),
    ],
    action=RuleAction.INTERRUPT_BUILD,
)

GitMergeConflict = Rule(
    name="GitMergeConflict",
    conditions=[
        Condition(
            context_element="step",
            target_attribute=["output", "lines"],
            matches_regex="(not something we can merge|Automatic merge failed; fix conflicts)",
        ),
    ],
    action=RuleAction.INTERRUPT_BUILD,
)


YarnDependencyNotResolved = Rule(
    name="YarnDependencyNotResolved",
    conditions=[
        Condition(
            context_element="step",
            target_attribute="name",
            matches_value="node_modules",
        ),
        Condition(
            context_element="step",
            target_attribute=["output", "lines"],
            contains_string="Couldn't find any versions for",
        ),
    ],
    action=RuleAction.INTERRUPT_BUILD,
)


wf_project_vi = RuleSet(
    name="wf_project_vi_pr",
    rules=[
        ValidateDocsPrettified,
        SlackServerError,
        GitBranchNameInvalidForGKEDeploy,
        SamizdatConnectionError,
        GitMergeConflict,
        YarnDependencyNotResolved,
    ],
    default_conditions=[
        Condition(
            context_element="build",
            target_attribute="link",
            contains_string="nytm/wf-project-vi",
        ),
        Condition(
            context_element="step",
            target_attribute="status",
            matches_value=["failed", "running"],
        ),
        Condition(
            context_element="step", target_attribute="exit_code", matches_value=0
        ),
    ],
    default_action=RuleAction.NEXT_STEP,
    default_notify=["slack"],
)
