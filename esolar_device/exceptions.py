class ESolarException(Exception):
    pass


class CommandNotAcknowledgedException(ESolarException):
    pass


class InvalidCommandException(ESolarException):
    pass


class ChecksumException(ESolarException):
    pass


class ReadTimeoutException(ESolarException):
    pass
