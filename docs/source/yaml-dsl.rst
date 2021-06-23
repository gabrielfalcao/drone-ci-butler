.. _yaml dsl:

Example Yaml DSL
~~~~~~~~~~~~~~~~~~

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
