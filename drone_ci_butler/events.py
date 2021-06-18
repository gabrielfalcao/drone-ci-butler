from blinker import signal
from drone_ci_butler.logs import get_logger


http_cache_hit = signal("http-cache-hit")
http_cache_miss = signal("http-cache-miss")
get_build_step_output = signal("get-build-step-output")
get_build_info = signal("get-build-info")
get_builds = signal("get-builds")
iter_builds_by_page = signal("iter-builds-by-page")

user_created = signal("user-created")
user_updated = signal("user-updated")

token_created = signal("token-created")
token_updated = signal("token-updated")
github_event = signal("github-event")


logger = get_logger("system-events")
