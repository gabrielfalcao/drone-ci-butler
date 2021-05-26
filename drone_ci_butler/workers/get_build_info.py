from .puller import PullerWorker


class GetBuildInfoWorker(PullerWorker):
    __log_name__ = 'build-info-retriever'

    def process_job(self, info: dict):
        build_id = info.get("build_id")

        missing_fields = []

        if not build_id:
            missing_fields.append("build_id")

        if missing_fields:
            self.logger.error(f"missing fields: {missing_fields} in {info}")
            return

        self.fetch_data(self.github_owner, self.github_repo, build_id)


    def fetch_data(self, owner: str, repo: str, build_id: int):
        try:
            build = self.api.get_build_info(owner, repo, build_id)
        except Exception as e:
            self.logger.exception(f'failed to retrieve build {owner}/{repo} {build_id}')
            return

        if '/pull' not in (build.link or ""):
            self.logger.info(f'ignoring non pull-request build {build.number} by {build.author_name}')
        else:
            self.logger.info(f'retrieving logs for build {build.number} {build.link}')

        # build = self.api.inject_logs_into_build(owner, repo, build)
        # for stage in failed_stages:
        #     self.publish(
        #         "build:failed",
        #     )
        # # 1. Poll zmq for job with build_id
        # # 2. Iterate over failed stages
        # # 3. For each failed stage check whether a failure notification was already sent
        # #      otherwise publish zmq event "stage failed" which will store this information in the db to prevent emitting the event twice
        # # 4. Iterate over pending stages (finished_at == None)
        # # 5. For each pending stage schedule a new job to monitor build_id
        # # 6. If the build has all its stages completed with success in all steps
        # #      then publish zmq event "build succeeded" which will store this information to the db to prevent emitting the event twice
        # pass
