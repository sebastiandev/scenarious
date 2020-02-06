import yaml
import six
import traceback
from functools import partial
from collections import OrderedDict

from .errors import BaseError
from .reference_handler import ReferenceHandler
from .store_handler import EntityStore
from .type_handlers.base import TypeHandlerException


class ScenariousException(BaseError):
    pass


class Scenario(object):

    @classmethod
    def load(cls, sources, type_handlers, load_priority=None, reference_handler=None, entity_store=None, autobuild=True):
        """
        Builds the Scenario based on the scenario definition stored in source, using the provided type handlers
        :param sources: A list of config file path or config file object to load the scenario from or a dict already built
        :param type_handlers: A list of handlers for every supported type
        :param load_priority: A list of type_names to be loaded first
        :param reference_handler: A reference parser
        :param entity_store: An entity store that handles object mapping and retrieval
        :return: A Scenario
        """

        type_handlers_by_name = {}
        for th in type_handlers:
            names = th.__type_name__ if type(th.__type_name__) in [list, tuple] else [th.__type_name__, th.__type_name__ + 's']
            type_handlers_by_name.update({name: th for name in names})

        reference_handler = reference_handler or ReferenceHandler()
        entity_store = entity_store or EntityStore()

        if not isinstance(sources, list):
            sources = [sources]

        return cls(sources, type_handlers_by_name, reference_handler=reference_handler, entity_store=entity_store,
                   load_priority=load_priority, autobuild=autobuild)

    def __init__(self, sources, handlers_by_type_name, reference_handler, entity_store, load_priority=None, autobuild=True):
        self._raw_data = {}
        self._type_handlers = handlers_by_type_name
        self._ref_handler = reference_handler
        self._entity_store = entity_store
        self._load_priority = load_priority or []
        self.update_multiple(sources)

        if autobuild:
            self.build()

    def update_multiple(self, sources):
        for s in sources:
            self.update(s)

    def update(self, source):
        if isinstance(source, dict):
            raw = source
        else:
            raw = yaml.load(open(source) if isinstance(source, six.string_types) else source)

        for entity, value in (raw or {}).items():
            objects = [{}] * value if isinstance(value, int) else value
            self._raw_data[entity] = self._raw_data.get(entity, []) + objects

    def build(self):
        for _type in self._load_priority:
            self._load_type_definition(self._get_type_name(_type))

        for _type, type_def in iter(self._raw_data.items()):
            if _type not in self._load_priority:
                self._load_type_definition(self._get_type_name(_type), type_def)

    def __getattr__(self, key):
        """
        Allow to access objects by type_name directly and provide support to
        dynamically add objects by type name.

        Access objects by type:
         > scenario.users

        Add objects by type:
         > scenario.add_user(**data)

        :param key:
        :return: object
        """
        if key.startswith('add_'):
            type_name = key.replace('add_', '')
            if self._entity_store.has_type(self._get_type_name(type_name)):
                return partial(self._create_obj, type_name)

            else:
                raise ScenariousException("Invalid type name '{}'".format(type_name))

        else:
            type_name = self._get_type_name(key)

            if self._entity_store.has_type(type_name):
                return list(self._entity_store.all(type_name))

            else:
                raise AttributeError("%s doesn't have type '%s'" % (self.__class__.__name__, type_name))

    def _get_type_name(self, name):
        return name.rstrip('s')

    def _get_type_handler(self, name):
        # We try name and name without last letter, in case plural is used
        handler = self._type_handlers.get(name, self._type_handlers.get(self._get_type_name(name), None))
        if not handler:
            raise ScenariousException("Invalid type name, no TypeHandler could be found for type '{}'".format(name))

        return handler

    def _create_obj(self, type_name, data, special_methods=None):
        handler = self._get_type_handler(type_name)

        obj_id, obj_def = self._entity_store.parse_obj_def(data)
        new_obj_def = self._process_references_and_methods(type_name, obj_def, special_methods or [])
        new_obj = handler.create(**new_obj_def)

        self._entity_store.add(new_obj, type_name=type_name, entity_id=obj_id)

        return new_obj

    def _resolve_reference(self, ref):
        """
        Resolves an object reference by getting the object and accessing any specified attributes.

        References are built like:
          $[type_name]_[id].[attribute]  The attribute can be a chain of attr calls
        Ex.
          $person_1.name => gets the object of type 'person' with ref/id 1 and from it retrieves the name attribute

        :param ref:
        :return: the resolved reference
        """
        ref_key_type, ref_key_id, ref_attrs = self._ref_handler.parse(ref)

        # We might have not loaded a needed dependency yet, so try to load it first
        if not self._entity_store.has_type(ref_key_type):
            try:
                self._load_type_definition(ref_key_type)
            except Exception as e:
                ScenariousException.reraise("Reference error, couldn't find type '{}'".format(ref_key_type), e)

        value = self._entity_store.get(ref_key_type, ref_key_id)
        for attr in ref_attrs:
            value = getattr(value, attr)

        return value

    def _load_type_definition(self, type_name, type_def=None):
        type_def = type_def or self._raw_data.get(type_name, self._raw_data[type_name+"s"])

        if not self._entity_store.has_type(type_name):
            if type(type_def) is list:
                for data in type_def:
                    self._load_type(type_name, data)

            elif type(type_def) is dict:
                self._load_type(type_name, type_def)

            elif type(type_def) is int:
                for _ in range(type_def):
                    self._load_type(type_name, {})
            else:
                raise ScenariousException(
                    "Type definition '{}' must be a list, dict or int. Got '{}' instead"
                        .format(type_name, type(type_def)))

    def _load_type(self, type_name, type_def):
        try:
            special_methods = []
            new_obj = self._create_obj(type_name, type_def, special_methods=special_methods)

            # Apply all special methods to the new object
            for method, param in special_methods:
                params = [new_obj]

                if isinstance(param, six.string_types):
                    params.append(self._resolve_reference(param) if self._ref_handler.is_reference(param) else param)

                elif type(param) in (list, tuple):
                    params.extend(param)

                else:
                    params.append(param)

                method(*params)
        except (TypeHandlerException, ScenariousException):
            raise

        except Exception as e:
            ScenariousException.reraise("Error loading type '{}'. Detail: {}".format(type_name, e), e)

    def _process_references_and_methods(self, type_name, obj_def, special_methods):
        if type(obj_def) is not dict:
            resolved_def = self._resolve_reference(obj_def) if self._ref_handler.is_reference(obj_def) else obj_def

        else:
            # Recursively iterate over a type_def converting references and tracking special methods
            resolved_def = dict(obj_def)

            for k, v in obj_def.items():
                handler = self._get_type_handler(type_name)

                if handler.is_method(k):
                    special_methods.append((handler.get_special_method(k), v))

                elif isinstance(v, (dict, OrderedDict)):
                    resolved_def[k] = self._process_references_and_methods(type_name, v, special_methods)

                elif isinstance(v, (list, tuple)):
                    resolved_def[k] = [self._process_references_and_methods(type_name, e, special_methods) for e in v]

                elif self._ref_handler.is_reference(v):
                    resolved_def[k] = self._resolve_reference(v)

        return resolved_def

    def by_id(self, type_name, ref_id):
        type_name = self._get_type_name(type_name)
        if not self._entity_store.has_type(type_name):
            raise KeyError("{} doesn't have elements of type '{}'".format(self.__class__.__name__, type_name))

        return self._entity_store.get(type_name, ref_id)
