import unittest
from uuid import uuid4
from random import randint

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from scenarious.util import DictObject
from scenarious.type_handlers.base import faker, TypeHandlerException
from scenarious import Scenario, TypeHandler


class TestTypeHandler(TypeHandler):

    @classmethod
    def _do_create(cls, data):
        data['id'] = str(uuid4())
        return DictObject(**data)


class TypeHandlerTest(unittest.TestCase):

    def test_fail_when_defaulting_a_required_field(self):
        class BadActorTypeHandler(TestTypeHandler):
            __type_name__ = 'actor'
            __requires__ = ['name']

            age = lambda: randint(18, 80)
            name = lambda: 'test name'

        self.assertRaises(TypeHandlerException, BadActorTypeHandler)

    def test_fail_when_missing_required_field(self):
        class ActorTypeHandler(TestTypeHandler):
            __type_name__ = 'actor'
            __requires__ = ['name']

            age = lambda: randint(18, 80)

        self.assertRaises(TypeHandlerException, ActorTypeHandler.validate_data, dict(age=30))
