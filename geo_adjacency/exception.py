"""
Custom exceptions.
"""


class ImmutablePropertyError(BaseException):
    """
    Raise when a property is immutable because the setter does nothing.
    """

    def __init__(self, message):
        super().__init__(message)
