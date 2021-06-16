from drone_ci_butler.slack import SlackClient
from drone_ci_butler.sql.models.drone import DroneBuild
from drone_ci_butler.sql.models.user import User
from drone_ci_butler.drone_api.models import BuildContext
from drone_ci_butler.rule_engine.default_rules import wf_project_vi
from .puller import PullerWorker


# 1. Poll zmq for job with build_id
# 2. Iterate over failed stages
# 3. For each failed stage check whether a failure notification was already sent
#      otherwise publish zmq event "stage failed" which will store this information in the db to prevent emitting the event twice
# 4. Iterate over pending stages (finished_at == None)
# 5. For each pending stage schedule a new job to monitor build_id
# 6. If the build has all its stages completed with success in all steps
#      then publish zmq event "build succeeded" which will store this information to the db to prevent emitting the event twice


class GetBuildInfoWorker(PullerWorker):
    __log_name__ = "build-info-retriever"

    def process_job(self, info: dict):
        build_id = info.get("build_id")

        missing_fields = []

        if not build_id:
            missing_fields.append("build_id")

        if missing_fields:
            self.logger.error(f"missing fields: {missing_fields} in {info}")
            return

        self.logger.info(f"processing job {info}")
        self.fetch_data(self.github_owner, self.github_repo, build_id)

    def fetch_data(self, owner: str, repo: str, build_id: int):
        try:
            build = self.api.get_build_info(owner, repo, build_id)
        except Exception as e:
            self.logger.exception(f"failed to retrieve build {owner}/{repo} {build_id}")
            return

        if "/pull" not in (build.link or ""):
            self.logger.debug(
                f"ignoring non pull-request build {build.number} by {build.author_name}"
            )
            return

        pr_number = build.link.split("/")[-1]
        if build.status not in ("running", "failure"):
            self.logger.info(
                f"ignoring {build.status} build {build.number} of PR #{pr_number} by {build.author_name}"
            )
            return

        build = self.api.inject_logs_into_build(owner, repo, build)
        stored = DroneBuild.get_or_create_from_drone_api(
            build.author_login, build.source_repo, build.number, build
        )

        def notify(message, stage, step, output):
            print(message)
            # author = User.find_one_by(github_username=build.author_login)
            # if not author:
            #     # ignore builds from github users who did not opt-in
            #     return

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔴 Build failed for the PR {pr_number} {owner}/{repo}",
                        "emoji": True,
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"**Stage:** stage.name"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"**Step:** step.name"},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{message}"},
                },
                {"type": "divider"},
            ]

            client = SlackClient().slack
            channel = "C023Z62N59Q"
            user_id = "W01BD07TYGP"
            self.logger.info(f"posting message to slack user @falcao")
            message_response = client.chat_postMessage(
                channel=user_id,
                blocks=blocks,
            )

        for stage in build.failed_stages():

            for step in stage.failed_steps():

                context = BuildContext(
                    build=build,
                    stage=stage,
                    step=step,
                )
                matches = wf_project_vi.apply(context)

                if matches:
                    message = "\n".join([t.to_description() for t in matches])
                    notify(message, stage, step, step.to_markdown())

                elif "http-status-check" in str(output.lines) and "🖤 404" in str(
                    output.lines
                ):
                    message = "**http-status-check** failed for {step.to_markdown()}"
                    notify(message, stage, step, step.output)
                    continue
                # print(f"failed step: \033[1;31m{step.to_string()}\033[0m")
                # notify(
                #     f"Unhandled ",
                #     stage,
                #     step,
                #     step.to_markdown(),
                # )
