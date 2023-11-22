class ImmutablePropertyError(BaseException):

    def __init__(self, message):
        super().__init__(message)