import six
import sys


def reraise(exc_type, msg, inner_ex):
    if sys.version_info[:2] >= (3, 2):
        six.raise_from(exc_type(msg), inner_ex)
    else:
        six.reraise(exc_type, msg, sys.exc_info()[2])


class BaseError(Exception):
    @classmethod
    def reraise(cls, msg, inner_ex):
        reraise(cls, msg, inner_ex)
