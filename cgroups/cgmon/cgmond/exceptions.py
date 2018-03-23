
class ExternalInvocationException(Exception):
    def __init__(self, errno, message):
        super(ExternalInvocationException, self).__init__(message)
        self.errno = errno
