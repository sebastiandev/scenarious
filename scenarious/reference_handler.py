import six

from .errors import BaseError


class ReferenceException(BaseError):
    pass


class ReferenceHandler(object):

    REFERENCE = '$'

    @classmethod
    def is_reference(cls, value):
        return value.startswith(cls.REFERENCE) if isinstance(value, six.string_types) else False

    @classmethod
    def parse(cls, ref):
        try:
            ref_parts = ref.split('.')
            ref_key = ref_parts[0][1:]

            ref_key_parts = ref_key.split('_')
            ref_key_type = '_'.join(ref_key_parts[:-1])
            ref_key_id = ref_key_parts[-1]

            ref_attrs = ref_parts[1:] if len(ref_parts) > 1 else []

            return ref_key_type, ref_key_id, ref_attrs

        except Exception as e:
            ReferenceException.reraise("Invalid reference '{}'".format(ref), e)
