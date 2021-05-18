import httpretty
from pathlib import Path
from vcr import VCR
from sure import scenario
from drone_ci_butler.drone_api import DroneAPIClient
from drone_ci_butler.drone_api.models import Build, OutputLine, Step, Stage, Output

functional_tests_path = Path(__file__).parent.absolute()
vcr = VCR(
    cassette_library_dir=str(functional_tests_path.joinpath(".cassetes")),
    # record_mode="once",
)


def prepare_client(context):
    context.client = DroneAPIClient(
        url="https://drone.dv.nyt.net/api/user",
        access_token="VIiQwPXd3YdxtAzkjl1S7rUUxaQh9PMy",
        sqlite_cache_file=functional_tests_path.joinpath("api-cache.sqlite"),
    )


def disconnect_client(context):
    context.client.close()


with_client = scenario(prepare_client, disconnect_client)


@vcr.use_cassette("api/repos/nytm/wf-project-vi/builds:GET:200.yaml")
@with_client
def test_drone_api_client_get_builds(context):
    "GET /api/repos/{owner}/{repo}/builds"

    # Given that I request the list of builds
    builds = context.client.get_builds("nytm", "wf-project-vi")

    # Then it should return a Build.List
    builds.should.be.a(Build.List)

    # And should have x items
    builds.should.have.length_of(25)


@vcr.use_cassette("api/repos/nytm/wf-project-vi/builds/:GET:200.yaml")
@with_client
def test_drone_api_client_get_build_info(context):
    "GET /api/repos/{owner}/{repo}/builds/{build}"

    # Given I request the list of builds
    build = context.client.get_build_info("nytm", "wf-project-vi", "137019")

    # Then it should return a Build
    build.should.be.a(Build)

    build.stages.should.have.length_of(8)
    stage_names = [s.name for s in build.stages]
    stage_names.should.equal(
        [
            "test",
            "build",
            "acceptance_tests",
            "performance_test",
            "pre_deployment_check",
            "deployment",
            "post_deployment_check",
            "metrics",
        ]
    )


@vcr.use_cassette("api/repos/nytm/wf-project-vi/builds/137019/logs/3/9:GET:200.yaml")
@with_client
def test_drone_api_client_get_build_step_log(context):
    "GET /api/repos/{owner}/{repo}/builds/{build}/logs/{stage}/{step}"

    # Given I request the list of builds
    output = context.client.get_build_step_output("nytm", "wf-project-vi", 137019, 3, 9)

    # Then it should return an Output
    output.should.be.an(Output)

    # And should have X items
    output.lines.should.have.length_of(27)


@vcr.use_cassette("get_build_with_logs.yaml")
@with_client
def test_drone_api_client_get_build_with_failed_stages(context):
    "DroneAPIClient.get_build_with_logs().failed_stages()"

    # Given I request the list of builds
    build = context.client.get_build_with_logs("nytm", "wf-project-vi", 137019)

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed stages
    failed_stages = build.failed_stages()

    failed_stages.should.be.a(Stage.List)

    failed_stages.should.have.length_of(2)
    failed_stages[0].name.should.equal("acceptance_tests")
    failed_stages[1].name.should.equal("post_deployment_check")


@vcr.use_cassette("get_build_with_logs.yaml")
@with_client
def test_drone_api_client_get_build_with_failed_steps(context):
    "DroneAPIClient.get_build_with_logs().failed_steps()"

    # Given I request the list of builds
    build = context.client.get_build_with_logs("nytm", "wf-project-vi", 137019)

    # Then it should return a Build
    build.should.be.a(Build)

    # And should return the failed steps
    failed_steps = build.failed_steps()

    failed_steps.should.be.a(Step.List)

    failed_steps.should.have.length_of(2)
    step1, step2 = failed_steps
    step1.name.should.equal("acceptance_tests_test_smartphone")
    step2.name.should.equal("acceptance_tests_test_tablet")

    step1.output.should.be.an(Output)
    step2.output.should.be.an(Output)

    step1.output.to_string().should.equal(
        '\r0:0:+ yarn test:acceptance smartphone --color\n\r1:1:\x1b[2K\x1b[1G\x1b[1myarn run v1.22.4\x1b[22m\n\r1:2:\x1b[2K\x1b[1G\x1b[2m$ BABEL_ENV=test ./tools/puppet-theater/conf/print && jest --runInBand --forceExit --config=test/jest.acceptance.config.js smartphone --color\x1b[22m\n\r1:3:\n\r1:4:Starting puppet-theater 🎭 with configuration:\n\r1:5:- \x1b[1mbaseUrl\x1b[22m\x1b[0m: \x1b[1;33m"http://vi.nytimes.com:3000"\x1b[0m\n\r1:6:- \x1b[1mheadless\x1b[22m\x1b[0m: \x1b[1;33mtrue\x1b[0m\n\r1:7:- \x1b[1mdebug\x1b[22m\x1b[0m: \x1b[1;33mfalse\x1b[0m\n\r1:8:- \x1b[1mdumpio\x1b[22m\x1b[0m: \x1b[1;33mfalse\x1b[0m\n\r1:9:- \x1b[1mbail\x1b[22m\x1b[0m: \x1b[1;33mtrue\x1b[0m\n\r1:10:- \x1b[1mverbose\x1b[22m\x1b[0m: \x1b[1;33mfalse\x1b[0m\n\r1:11:- \x1b[1mexecutablePath\x1b[22m\x1b[0m: \x1b[1;33m"/usr/bin/google-chrome-stable"\x1b[0m\n\r1:12:- \x1b[1mprintConf\x1b[22m\x1b[0m: \x1b[1;33mtrue\x1b[0m\n\r1:13:- \x1b[1mwindowWidth\x1b[22m\x1b[0m: \x1b[1;33m1920\x1b[0m\n\r1:14:- \x1b[1mwindowHeight\x1b[22m\x1b[0m: \x1b[1;33m1080\x1b[0m\n\r1:15:\n\r2:16:\x1b[1mNo tests found, exiting with code 1\x1b[22m\n\r2:17:Run with `--passWithNoTests` to exit with code 0\n\r2:18:In \x1b[1m/drone/src\x1b[22m\n\r2:19:  3923 files checked.\n\r2:20:  roots: \x1b[33m/drone/src/src, /drone/src/tools/webpack, /drone/src/tools/eslint, /drone/src/tools/puppet-theater, /drone/src/tools/wait-for-service\x1b[39m - 3923 matches\n\r2:21:  testMatch: \x1b[33m**/*desktop.acceptance.js, **/*tablet.acceptance.js, **/*smartphone.acceptance.js\x1b[39m - 1 match\n\r2:22:  testPathIgnorePatterns: \x1b[33m.*/testing/.*, .*fixture.*, /[.]caches/, /build/, /lib/, /docs/, /docs_build/, /node_modules/, /perf/, /schema[.]json, /src/network/finagle-utils/__tests__/finagle-utils[.]fixtures[.]js, /src/public/, /src/server/__tests__/setup.fixtures.*, /src/shared/Iframe/polyfill/, .*ab-test.js\x1b[39m - 3726 matches\n\r2:23:  testRegex:  - 0 matches\n\r2:24:Pattern: \x1b[33msmartphone\x1b[39m - 0 matches\n\r2:25:\x1b[2K\x1b[1G\x1b[31merror\x1b[39m Command failed with exit code 1.\n\r2:26:\x1b[2K\x1b[1G\x1b[34minfo\x1b[39m Visit \x1b[1mhttps://yarnpkg.com/en/docs/cli/run\x1b[22m for documentation about this command.\n'
    )
    step2.output.to_string().should.equal(
        '\r0:0:+ yarn test:acceptance tablet --color\n\r1:1:\x1b[2K\x1b[1G\x1b[1myarn run v1.22.4\x1b[22m\n\r1:2:\x1b[2K\x1b[1G\x1b[2m$ BABEL_ENV=test ./tools/puppet-theater/conf/print && jest --runInBand --forceExit --config=test/jest.acceptance.config.js tablet --color\x1b[22m\n\r1:3:\n\r1:4:Starting puppet-theater 🎭 with configuration:\n\r1:5:- \x1b[1mbaseUrl\x1b[22m\x1b[0m: \x1b[1;33m"http://vi.nytimes.com:3000"\x1b[0m\n\r1:6:- \x1b[1mheadless\x1b[22m\x1b[0m: \x1b[1;33mtrue\x1b[0m\n\r1:7:- \x1b[1mdebug\x1b[22m\x1b[0m: \x1b[1;33mfalse\x1b[0m\n\r1:8:- \x1b[1mdumpio\x1b[22m\x1b[0m: \x1b[1;33mfalse\x1b[0m\n\r1:9:- \x1b[1mbail\x1b[22m\x1b[0m: \x1b[1;33mtrue\x1b[0m\n\r1:10:- \x1b[1mverbose\x1b[22m\x1b[0m: \x1b[1;33mfalse\x1b[0m\n\r1:11:- \x1b[1mexecutablePath\x1b[22m\x1b[0m: \x1b[1;33m"/usr/bin/google-chrome-stable"\x1b[0m\n\r1:12:- \x1b[1mprintConf\x1b[22m\x1b[0m: \x1b[1;33mtrue\x1b[0m\n\r1:13:- \x1b[1mwindowWidth\x1b[22m\x1b[0m: \x1b[1;33m1920\x1b[0m\n\r1:14:- \x1b[1mwindowHeight\x1b[22m\x1b[0m: \x1b[1;33m1080\x1b[0m\n\r1:15:\n\r2:16:\x1b[1mNo tests found, exiting with code 1\x1b[22m\n\r2:17:Run with `--passWithNoTests` to exit with code 0\n\r2:18:In \x1b[1m/drone/src\x1b[22m\n\r2:19:  3923 files checked.\n\r2:20:  roots: \x1b[33m/drone/src/src, /drone/src/tools/webpack, /drone/src/tools/eslint, /drone/src/tools/puppet-theater, /drone/src/tools/wait-for-service\x1b[39m - 3923 matches\n\r2:21:  testMatch: \x1b[33m**/*desktop.acceptance.js, **/*tablet.acceptance.js, **/*smartphone.acceptance.js\x1b[39m - 1 match\n\r2:22:  testPathIgnorePatterns: \x1b[33m.*/testing/.*, .*fixture.*, /[.]caches/, /build/, /lib/, /docs/, /docs_build/, /node_modules/, /perf/, /schema[.]json, /src/network/finagle-utils/__tests__/finagle-utils[.]fixtures[.]js, /src/public/, /src/server/__tests__/setup.fixtures.*, /src/shared/Iframe/polyfill/, .*ab-test.js\x1b[39m - 3726 matches\n\r2:23:  testRegex:  - 0 matches\n\r2:24:Pattern: \x1b[33mtablet\x1b[39m - 0 matches\n\r2:25:\x1b[2K\x1b[1G\x1b[31merror\x1b[39m Command failed with exit code 1.\n\r2:26:\x1b[2K\x1b[1G\x1b[34minfo\x1b[39m Visit \x1b[1mhttps://yarnpkg.com/en/docs/cli/run\x1b[22m for documentation about this command.\n'
    )
