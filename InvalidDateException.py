__author__ = 'Chris Ward'


class InvalidDateException(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
