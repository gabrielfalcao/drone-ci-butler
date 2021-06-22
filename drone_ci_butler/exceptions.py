class UserFriendlyException(Exception):
    """subclasses of this exception *MUST* provide error messages that can
    be "printed" to the user without need for full traceback"""


class ConfigMissing(UserFriendlyException):
    def __init__(self, key, filename, env: str = None):
        env = ""
        if env:
            env = f" or from env var {env}"

        msg = f"Config key {key} missing from {filename}{env}"
        super().__init__(msg)
