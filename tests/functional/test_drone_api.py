import httpretty
from pathlib import Path
from vcr import VCR
from sure import scenario
from drone_ci_butler.drone_api import DroneAPIClient
from drone_ci_butler import sql
from drone_ci_butler.config import config
from drone_ci_butler.drone_api.models import Build, OutputLine, Step, Stage, Output

functional_tests_path = Path(__file__).parent.absolute()

vcr = VCR(
    cassette_library_dir=str(functional_tests_path.joinpath(".cassetes")),
    record_mode="new_episodes",
)


def prepare_client(context):
    context.metadata = sql.setup_db()
    context.client = DroneAPIClient.from_config(config)


def disconnect_client(context):
    context.client.close()


with_client = scenario(prepare_client, disconnect_client)


@vcr.use_cassette
@with_client
def test_drone_api_client_get_builds(context):
    "GET /api/repos/{owner}/{repo}/builds"
    # Given that I request the list of builds
    builds = context.client.get_builds(
        None,  # use owner from drone-ci-butler.yml
        None,  # use repo from drone-ci-butler.yml
    )

    # Then it should return a Build.List
    builds.should.be.a(Build.List)

    # And should have x items
    builds.should.have.length_of(4)


@vcr.use_cassette
@with_client
def test_drone_api_client_get_build_info(context):
    "GET /api/repos/{owner}/{repo}/builds/{build}"

    # Given I request the list of builds
    build = context.client.get_build_info("drone-ci-monitor", "drone-ci-monitor", "1")

    # Then it should return a Build
    build.should.be.a(Build)

    build.stages.should.have.length_of(2)
    stage_names = [s.name for s in build.stages]
    stage_names.should.equal(
        [
            "webhook",
            "test",
        ]
    )


@vcr.use_cassette
@with_client
def test_drone_api_client_get_build_step_log(context):
    "GET /api/repos/{owner}/{repo}/builds/{build}/logs/{stage}/{step}"

    # Given I request the list of builds
    output = context.client.get_build_step_output(
        "drone-ci-monitor", "drone-ci-monitor", 1, 1, 1
    )

    # Then it should return an Output
    output.should.be.an(Output)

    # And should have X items
    output.lines.should.have.length_of(10)


# @vcr.use_cassette
# @with_client
# def test_drone_api_client_get_build_step_log_skipped(context):
#     "get_build_step_output() with a skipped step should throw error"

#     # Given I request the list of builds
#     output = context.client.get_build_step_output(
#         "drone-ci-monitor", "drone-ci-monitor", 1, 1, 1
#     )

#     # Then it should return an Output
#     output.should.be.none


@vcr.use_cassette
@with_client
def test_drone_api_client_get_build_with_failed_stages(context):
    "DroneAPIClient.get_build_with_logs().failed_stages()"

    # Given I request the list of builds
    build = context.client.get_build_with_logs(
        "drone-ci-monitor", "drone-ci-monitor", 1
    )

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed stages
    failed_stages = build.failed_stages()

    failed_stages.should.be.a(Stage.List)

    failed_stages.should.have.length_of(2)
    failed_stage_numbers = [s.number for s in failed_stages]
    failed_stage_names = [s.name for s in failed_stages]

    failed_stage_names.should.equal(
        [
            "webhook",
            "test",
        ]
    )
    failed_stage_numbers.should.equal([1, 2])


@vcr.use_cassette
@with_client
def test_drone_api_client_get_build_with_failed_steps(context):
    "DroneAPIClient.get_build_with_logs().failed_steps()"

    # Given I request the list of builds
    build = context.client.get_build_with_logs(
        "drone-ci-monitor", "drone-ci-monitor", 1
    )

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed steps
    failed_steps = build.failed_steps()

    failed_steps.should.be.a(Step.List)

    failed_steps.should.have.length_of(1)
    (step1,) = failed_steps
    step1.name.should.equal("send")

    step1.output.should.be.an(Output)

    step1.output.to_string().should.equal(
        "\r0:latest: Pulling from plugins/webhook\n\r1:Digest: sha256:a862b76d5c51eade0372a1d4d82c4ac7c7d186eef0dbf61ca01bcd51f17d275d\n\r2:Status: Downloaded newer image for plugins/webhook:latest\n\r3:Error: Failed to execute the HTTP request. Post https://drone-ci-butler.ngrok.io/hooks/drone: local error: tls: bad record MAC\n\r4:2021/06/21 22:53:15 Post https://drone-ci-butler.ngrok.io/hooks/drone: local error: tls: bad record MAC\n"
    )
    str(step1.output.lines).should.equal(
        "latest: Pulling from plugins/webhook\n\nDigest: sha256:a862b76d5c51eade0372a1d4d82c4ac7c7d186eef0dbf61ca01bcd51f17d275d\n\nStatus: Downloaded newer image for plugins/webhook:latest\n\nError: Failed to execute the HTTP request. Post https://drone-ci-butler.ngrok.io/hooks/drone: local error: tls: bad record MAC\n\n2021/06/21 22:53:15 Post https://drone-ci-butler.ngrok.io/hooks/drone: local error: tls: bad record MAC\n"
    )
    str(step1.output).should.equal(
        "latest: Pulling from plugins/webhook\n\nDigest: sha256:a862b76d5c51eade0372a1d4d82c4ac7c7d186eef0dbf61ca01bcd51f17d275d\n\nStatus: Downloaded newer image for plugins/webhook:latest\n\nError: Failed to execute the HTTP request. Post https://drone-ci-butler.ngrok.io/hooks/drone: local error: tls: bad record MAC\n\n2021/06/21 22:53:15 Post https://drone-ci-butler.ngrok.io/hooks/drone: local error: tls: bad record MAC\n"
    )


@vcr.use_cassette
@with_client
def test_drone_api_client_get_latest_build_with_log(context):
    "DroneAPIClient.get_latest_build()"

    # Given I request the list of builds
    build = context.client.get_latest_build(
        "drone-ci-monitor",
        "drone-ci-monitor",
        "main",
    )

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed steps
    failed_steps = build.failed_steps()

    failed_steps.should.be.a(Step.List)

    failed_steps.should.have.length_of(1)
    names = [s.name for s in failed_steps]

    names.should.equal(["webhook"])
