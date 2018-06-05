import types
import inspect
import six
from faker import Faker
from scenarious.util import module_dir, ModuleLoader

try:
    from dateparser import parse as dparse

except ImportError:
    from dateutil.parser import parse as dparse


faker = Faker()


class TypeHandlerException(Exception):
    pass


class TypeHandler(object):
    __type_name__ = None
    __requires__ = None

    def __init__(self, **kwargs):
        for k in self.requirements():
            if hasattr(self, k):
                raise TypeHandlerException("Field '{}' is required but also has a default value. "
                                           "Required fields cannot have default values".format(k))

    @classmethod
    def requirements(cls):
        """
        Gets the requirements from every handler's parent
        :return: list of required attributes
        """
        reqs = set(cls.__requires__ or [])

        for base in cls.__bases__:
            if hasattr(base, '__requires__'):
                for e in list(base.__requires__ or []):
                    reqs.add(e)

        return reqs

    @classmethod
    def validate_data(cls, data):
        missing = []

        for k in cls.requirements():
            if k not in data:
                missing.append(k)

        if missing:
            raise TypeHandlerException("{} Required fields '{}'  are missing".format(cls.__name__, ','.join(missing)))

    @classmethod
    def is_method(cls, attr):
        return attr.startswith('_')

    @classmethod
    def get_special_method(cls, value):
        return getattr(cls, value[1:]) if cls.is_method(value) else None

    @classmethod
    def create(cls, **kwargs):
        cls.validate_data(kwargs)

        handler = cls(**kwargs)
        data = cls._base_attributes(cls)
        data.update(dict(cls.__dict__))

        for k, v in dict(data).items():
            cls_attr = getattr(cls, k)
            if k.startswith('__') or (callable(cls_attr) and not isinstance(v, types.LambdaType)):
                data.pop(k)

            elif isinstance(v, types.LambdaType):
                data[k] = v()

        # First apply the user provided data
        data.update(**kwargs)

        # Finally update data with whatever the type handler constructor did
        # because it might build attributes based on the kwargs
        data.update(**handler.__dict__)

        cls._clean_data(data)
        cls._format_data(data)

        return cls._do_create(data)

    @classmethod
    def _base_attributes(cls, handler):
        """
        Gets the attributes from every handler's parent
        :param handler: Handler to inspect
        :return: dict of attributes
        """
        attrs = {}
        for base in handler.__bases__:
            attrs.update(base.__dict__)

        return attrs

    @classmethod
    def _clean_data(cls, data):
        pass

    @classmethod
    def _is_datetime_attribute(cls, attr):
        return False

    @classmethod
    def _parse_date(cls, date_str):
        return dparse(date_str)

    @classmethod
    def _format_data(cls, data):
        for attr, value in iter(data.items()):
            if isinstance(value, six.string_types) and cls._is_datetime_attribute(attr):
                data[attr] = cls._parse_date(value)

    @classmethod
    def _do_create(cls, data):
        raise NotImplementedError


class TypeHandlerLoader(ModuleLoader):

    group_path = module_dir(__file__)

    not_allowed_classes = [TypeHandler]

    @classmethod
    def is_allowed_class(cls, obj):
        return inspect.isclass(obj) and issubclass(obj, TypeHandler) and obj not in cls.not_allowed_classes
