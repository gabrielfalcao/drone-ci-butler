Drone-CI Butler
===============

A Python-based service that monitors Drone-CI builds looking for error
patterns and notifies the authors of specific failures as github PR
comments or slack messages.

It implements an engine that matches *Rulesets* against Drone Builds, Stages and Steps.

- A *Ruleset* has one or more *Rules*
- A *Rule* as one or more *Conditions*
- A *Condition* has one or more *Matchers*
- A *Matcher* works with properties the drone elements:

  - ``build``
  - ``stage``
  - ``step``

- A *Matcher* can check if an attribute:
  - Has an exact **value**
  - **Contains String**
  - matches a **regular expression**
  - **is not** an exact value.


.. image:: docs/source/_static/arch.png
  :alt: Architecture Overview


Domain-Specific Languages
-------------------------

The Rule Engine supports 2 DSL formats

- Python
- YAML


Example Python DSL
~~~~~~~~~~~~~~~~~~

.. code:: python


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
       action=RuleAction.NEXT_RULE,
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
       action=RuleAction.SKIP_ANALYSIS,
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
       action=RuleAction.SKIP_ANALYSIS,
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
       action=RuleAction.SKIP_ANALYSIS,
   )

   YarnDependencyNotResolved = Rule(
       name="YarnDependencyNotResolved",
       conditions=[
           Condition(
               context_element="step",
               target_attribute="name",
               matches_value="node_modules",
               required=True,
           ),
           Condition(
               context_element="step",
               target_attribute=["output", "lines"],
               matches_regex=r"Couldn't find any versions for\s*(\"([^\"]+)\" that matches \"([^\"]+)\")?",
               required=True,
           ),
       ],
       action=RuleAction.SKIP_ANALYSIS,
   )


   pull_requests_only = Condition(
       context_element="build",
       target_attribute="link",
       contains_string="/pull/",
       required=True,
   )
   build_matches_vi_project = Condition(
       context_element="build",
       target_attribute="link",
       contains_string="nytm/wf-project-vi",
       required=True,
   )
   step_failed_or_running = Condition(
       context_element="step",
       target_attribute="status",
       required=True,
       matches_value=[
           "fail*",
           "running",
       ],
   )
   step_exit_code_nonzero = Condition(
       context_element="step",
       target_attribute="exit_code",
       is_not=0,
       required=True,
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
       required_conditions=[
           build_matches_vi_project,
           pull_requests_only,
           step_failed_or_running,
       ],
       default_conditions=[
           step_exit_code_nonzero,
       ],
       default_action=RuleAction.NEXT_RULE,
       default_notify=["slack"],
   )


Example Yaml DSL
~~~~~~~~~~~~~~~~


.. code:: yaml

   rulesets:
     wf-project-vi:
       default-conditions:
         - build.link:
             contains_string: "nytm/wf-project-vi"
         - step.status: failed
         - step.exit_code:
             is_not:  0

       default_action: NEXT_RULE # default to continue analysis onto next step after matching a rule
       default_notify:
         - slack

       rules:
         - name: ValidateDocsPrettified
           when:
             - step.output:
                 matches_regex: "prettier:docs"
           action: NEXT_RULE

         - name: SlackServerError
           when:
             - step.name:
                 contains_string: "slack"
             - step.output:
                 contains_string: "server error"
           action: NEXT_RULE

         # skip build (and cancel it if still running)
         - name: GitBranchNameInvalidForGKEDeploy
           when:
             - step.output:
                 matches_regex: "prettier:docs"
           action: SKIP_ANALYSIS

         - name: GitMergeConflict
           when:
             - step.output:
                 matches_regex: "(not something we can merge|Automatic merge failed; fix conflicts)"

           action: SKIP_ANALYSIS

         - name: SamizdatConnectionError
           when:
             - step.output:
                 contains_string:
                   - "ECONNREFUSED"
                   - "samizdat"
           action: SKIP_ANALYSIS
           notify:
             - slack
             - github

         - name: YarnDependencyNotResolved
           when:
             - step.name:
                 contains_string: "node_modules"
             - step.output:
                 contains_string: "Couldn't find any versions for"

           action: SKIP_ANALYSIS
           notify:
             - slack
             - github
