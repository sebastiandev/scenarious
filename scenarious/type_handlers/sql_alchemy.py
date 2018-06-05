from datetime import date, datetime
from scenarious.type_handlers.base import TypeHandler, TypeHandlerLoader


class SQLAlchemyTypeHandlerException(Exception):
    pass


class SQLAlchemyTypeHandler(TypeHandler):

    __model__ = None

    @classmethod
    def get_attribute_type(cls, attr):
        from sqlalchemy.orm.attributes import InstrumentedAttribute
        from sqlalchemy.orm.properties import ColumnProperty

        attr_type = None
        attr = getattr(cls.__model__, attr)

        if hasattr(attr, 'type'):
            attr_type = attr.type.python_type

        elif isinstance(attr, InstrumentedAttribute):
            attr_type = attr.property.columns[0].type.python_type

        elif isinstance(attr, ColumnProperty):
            attr_type = attr.columns[0].type.python_type

        return attr_type

    @classmethod
    def _is_datetime_attribute(cls, attr):
        return cls.get_attribute_type(attr) in [datetime, date]

    @classmethod
    def _clean_data(cls, data):
        required_fields = cls.requirements()
        base_attrs = cls._base_attributes(cls)

        for k in data.keys():
            if k.startswith('__'):
                data.pop(k)

            elif not hasattr(cls.__model__, k) \
               and k not in cls.__model__.__dict__ \
               and k not in base_attrs \
               and k not in required_fields:
                raise SQLAlchemyTypeHandlerException("'{}' is not a required attribute nor an attribute from '{}'"
                                                     .format(k, cls.__model__.__class__.__name__))

    @classmethod
    def _do_create(cls, data):
        return cls.__model__.create(**data)


class SQLAlchemyTypeHandlerLoader(TypeHandlerLoader):

    not_allowed_classes = [TypeHandler, SQLAlchemyTypeHandler]
