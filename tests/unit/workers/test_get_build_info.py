import gevent

from unittest.mock import patch, Mock, call


from drone_ci_butler.workers.get_build_info import GetBuildInfoWorker


@patch("drone_ci_butler.workers.get_build_info.GetBuildInfoWorker.fetch_data")
def test_process_job_fetches_data(fetch_data):
    "GetBuildInfoWorker.process_job() should call fetch_data()"

    # Given a worker with dummy parameters
    worker = GetBuildInfoWorker(pull_connect_address="tcp://dummy:0", worker_id="dummy")
    worker.logger = Mock(name="logger")

    # When I call process_job()
    worker.process_job({"build_id": 1234, "ignore_filters": True})

    # Then it should call fetch_data with the configured params
    fetch_data.assert_called_once_with(
        "nytm", "wf-project-vi", 1234, ignore_filters=True
    )

    # And it should have logged INFO
    worker.logger.assert_has_calls(
        [
            call.debug("processing job {'build_id': 1234, 'ignore_filters': True}"),
            call.debug(
                "done processing job {'build_id': 1234, 'ignore_filters': True}"
            ),
        ]
    )
