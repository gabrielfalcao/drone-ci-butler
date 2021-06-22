import pytest
import httpretty
from pathlib import Path
from vcr import VCR
from sure import scenario
from uiclasses import DataBag
from drone_ci_butler.drone_api import DroneAPIClient
from drone_ci_butler import sql
from drone_ci_butler.config import config
from drone_ci_butler.drone_api.models import Build, OutputLine, Step, Stage, Output

functional_tests_path = Path(__file__).parent.absolute()

vcr = VCR(
    cassette_library_dir=str(functional_tests_path.joinpath(".cassetes")),
    record_mode="new_episodes",
)


def prepare_context():
    metadata = sql.setup_db(config)
    client = DroneAPIClient.from_config(config)
    return dict(
        client=client,
        metadata=metadata,
    )


def prepare_client(context):
    for key, value in prepare_context().items():
        setattr(context, key, value)


def disconnect_client(context):
    context.client.close()


@pytest.fixture
def context():
    return type("context", (DataBag,), prepare_context())


with_client = scenario(prepare_client, disconnect_client)


@vcr.use_cassette
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
    builds.should.have.length_of(16)


@vcr.use_cassette
def test_drone_api_client_get_build_info(context):
    "GET /api/repos/{owner}/{repo}/builds/{build}"

    # Given I request the list of builds
    build = context.client.get_build_info("drone-ci-monitor", "drone-api-tests", 4)

    # Then it should return a Build
    build.should.be.a(Build)

    build.stages.should.have.length_of(3)
    stage_names = [s.name for s in build.stages]
    stage_names.should.equal(
        [
            "success",
            "errors",
            "webhooks",
        ]
    )


@vcr.use_cassette
def test_drone_api_client_get_build_step_log(context):
    "GET /api/repos/{owner}/{repo}/builds/{build}/logs/{stage}/{step}"

    # Given I request the list of builds
    output = context.client.get_build_step_output(
        "drone-ci-monitor", "drone-api-tests", 3, 2, 1
    )

    # Then it should return an Output
    output.should.be.an(Output)

    # And should have X items
    output.lines.should.have.length_of(7)


# @vcr.use_cassette
# # def test_drone_api_client_get_build_step_log_skipped(context):
#     "get_build_step_output() with a skipped step should throw error"

#     # Given I request the list of builds
#     output = context.client.get_build_step_output(
#         "drone-ci-monitor", "drone-api-tests", 1, 1, 1
#     )

#     # Then it should return an Output
#     output.should.be.none


@vcr.use_cassette
def test_drone_api_client_get_build_with_stages(context):
    "DroneAPIClient.get_build_with_logs().stages"

    # Given I request the list of builds
    build = context.client.get_build_with_logs("drone-ci-monitor", "drone-api-tests", 1)

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed stages
    stages = build.stages

    stages.should.be.a(Stage.List)

    stages.should.have.length_of(3)
    stage_numbers = [s.number for s in stages]
    stage_names = [s.name for s in stages]

    stage_names.should.equal(
        [
            "success",
            "error",
            "webhooks",
        ]
    )
    stage_numbers.should.equal([1, 2, 3])


@vcr.use_cassette
def test_drone_api_client_get_build_with_failed_steps(context):
    "DroneAPIClient.get_build_with_logs().steps.filter(lambda step: step.exit_code != 0)"

    # Given I request the list of builds
    build = context.client.get_build_with_logs("drone-ci-monitor", "drone-api-tests", 5)

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed steps
    failed_steps = build.steps.filter(lambda step: step.exit_code != 0)
    failed_steps.should.be.a(Step.List)

    failed_steps.should.have.length_of(5)
    (step1, step2, step3, step4, step5) = failed_steps
    failed_step_names = [s.name for s in failed_steps]

    failed_step_names.should.equal(
        [
            "slack server error",
            "verify docs",
            "connection refused",
            "merge conflict",
            "yarn dependencies",
        ]
    )

    step2.output.should.be.an(Output)

    step3.output.to_string().should.equal(
        "\r0:+ echo -e \"connection refused\"\n\r1:connection refused\n\r2:+ echo -e 'samizdat ECONNREFUSED'\n\r3:samizdat ECONNREFUSED\n\r4:+ exit 1\n"
    )
    str(step4.output.lines).should.equal(
        "+ echo -e \"merge conflict\"\n\nmerge conflict\n\n+ echo -e 'Automatic merge failed; fix conflicts in your git branch'\n\nAutomatic merge failed; fix conflicts in your git branch\n\n+ exit 1\n"
    )
    str(step5.output).should.equal(
        '+ echo -e "yarn dependencies"\n\nyarn dependencies\n\n+ echo -e \'Couldn\'"\'"\'t find any versions for "react"\'\n\nCouldn\'t find any versions for "react"\n\n+ exit 1\n'
    )


@vcr.use_cassette
def test_drone_api_client_get_latest_build_with_log(context):
    "DroneAPIClient.get_latest_build()"

    # Given I request the list of builds
    build = context.client.get_latest_build(
        "drone-ci-monitor",
        "drone-api-tests",
        "main",
    )

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed steps
    steps = build.steps

    steps.should.be.a(Step.List)

    steps.should.have.length_of(13)
    names = [s.name for s in steps]

    names.should.equal(
        [
            "clone",
            "build",
            "unit tests",
            "integration tests",
            "component tests",
            "functional tests",
            "e2e tests",
            "clone",
            "slack server error",
            "verify docs",
            "connection refused",
            "merge conflict",
            "yarn dependencies",
        ]
    )
