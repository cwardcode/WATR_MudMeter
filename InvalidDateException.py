# Author: Chris Ward
# Date: 04/20/2015
# Version: 4/24/2015

class InvalidDateException(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
