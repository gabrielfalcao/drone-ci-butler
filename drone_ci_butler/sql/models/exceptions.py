class DatabaseException(Exception):
    """base exception for any problems raised from drone_ci_butler.sql"""


class BuildNotFound(DatabaseException):
    """raised when a build is not found"""
