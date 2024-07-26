"""Exceptions for calendar sync."""


class CalendarSyncException(Exception):
    """Base class for exceptions in this module."""


class ConfigDoesNotExistException(CalendarSyncException):
    """
    Exception for missing config file.

    Raised when load_config() is called in __init__ of Config class
    and the config file does not exist.
    """


class InvalidConfigException(CalendarSyncException):
    """
    Exception for invalid config file.

    Raised when load_config() is called and the config file is invalid.
    """


class ElementNotFoundException(CalendarSyncException):
    """Exception when crawler cannot locate an element."""


class SubmissionStatusError(CalendarSyncException):
    """Exception when submission status is unexpected."""
