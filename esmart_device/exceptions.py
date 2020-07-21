class ESmartException(Exception):
    pass


class CommandNotAcknowledgedException(ESmartException):
    pass


class InvalidCommandException(ESmartException):
    pass


class ChecksumException(ESmartException):
    pass


class ReadTimeoutException(ESmartException):
    pass
