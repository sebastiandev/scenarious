import six
from collections import defaultdict, OrderedDict


class EntityID(object):

    def __init__(self, identifier=None, alias=None):
        self.identifier = identifier
        self.alias = alias


class EntityStoreException(Exception):
    pass


class EntityStore(object):

    ID = 'id'
    ALIAS = '_alias'

    def __init__(self):
        self._objects = defaultdict(dict)
        self._aliased_objects = defaultdict(dict)
        self._objects_id_counter = defaultdict(lambda: 1)  # start off counter from 1

    @classmethod
    def parse_obj_def(cls, obj_def):
        return EntityID(obj_def.pop(cls.ID, None), obj_def.pop(cls.ALIAS, None)), obj_def

    def _relocate_object(self, obj_id, type_name):
        """
        Assigns a new id to the object referenced by obj_id by simply calculating
        the next available id for the type_name

        :param obj_id: id of the object to relocate
        :param type_name: object type
        :return:
        """
        previous_e = self._objects[type_name].pop(obj_id.identifier)
        new_id = self._objects_id_counter[type_name] + 1
        self._objects[type_name][new_id] = previous_e

    def _generate_id(self, type_name):
        """
        Generates an automatic id for a given type. It implements an incremental
        counter per type making sure that the generated id doesnt collied with an existing one
        that might have been assigned manually to a specific obj

        :param type_name: type name to generate id for
        :return:
        """
        while self._objects_id_counter[type_name] in self._objects[type_name]:
            self._objects_id_counter[type_name] += 1

        return self._objects_id_counter[type_name]

    def has_type(self, type_name):
        return type_name in self._objects

    def add(self, obj, type_name, entity_id=None):
        if not entity_id:
            entity_id = EntityID()

        if entity_id.alias in self._aliased_objects[type_name]:
            raise EntityStoreException("Duplicated alias for {}".format(type_name))

        if entity_id.identifier in self._objects[type_name]:
            self._relocate_object(entity_id, type_name)

        elif not entity_id or not entity_id.identifier:
            entity_id.identifier = self._generate_id(type_name)

        self._objects[type_name][entity_id.identifier] = obj

        if entity_id.alias:
            self._aliased_objects[type_name][entity_id.alias] = obj

        return entity_id

    def get(self, type_name, ref):
        e = self._aliased_objects.get(type_name, {}).get(ref, None) \
            or self._objects.get(type_name, {}).get(ref, None)

        try:
            if not e and type(ref) in [int, float]:
                e = self._objects.get(type_name, {}).get(six.string_types(ref), None)

            if not e and isinstance(ref, six.string_types):
                e = self._objects.get(type_name, {}).get(int(ref), None)

        except:
            pass

        return e

    def all(self, type_name):
        return self._objects.get(type_name, {}).values()
