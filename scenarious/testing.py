try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from functools import wraps
from .type_handlers.base import TypeHandlerLoader
from .scenario import Scenario


class ScenariousBaseTest(object):

    scenario_handler = Scenario
    type_handler_loader = TypeHandlerLoader

    def __init__(self, *args, **kwargs):
        self._scenario = None
        super(ScenariousBaseTest, self).__init__(*args, **kwargs)

    @classmethod
    def build_scenario(cls, data_stream=None, handlers=None, scenario_class=None):
        data = data_stream or {}

        if type(data_stream) is str:
            data = StringIO(data_stream)

        scenario_class = scenario_class or cls.scenario_handler
        return scenario_class.load(data, handlers or cls.type_handler_loader.load())

    def create_scenario(self, data_stream=None, handlers=None):
        self._scenario = self.build_scenario(data_stream, handlers)

    def __getattr__(self, item):
        if not hasattr(self, '_scenario'):
            raise AttributeError("ScenariousBaseTest doesnt have attribute {}".format(item))

        if hasattr(self._scenario, item):
            r = getattr(self._scenario, item)
            return r if item.endswith('s') else r[0]

        else:
            raise AttributeError("ScenariousBaseTest Scenario doesnt have attribute {}(s)".format(item))


def scenario(data_stream, handlers=None, scenario_class=None):

    def test_decorator(f):
        @wraps(f)
        def test_decorated(self, *args, **kwargs):
            # TODO: If we want to have a base scenario defined in the setUp
            # we might want to add the data from data_stream into that scenario
            # instead of just replace it

            if isinstance(self, ScenariousBaseTest):
                self.create_scenario(data_stream, handlers=handlers)
                f(self, *args, **kwargs)
            else:
                # If not using ScenariousBaseTest, then inject scenario as a test parameter
                kwargs['scenario'] = ScenariousBaseTest.build_scenario(data_stream,
                                                                       handlers=handlers,
                                                                       scenario_class=scenario_class)
                f(self, *args, **kwargs)

        return test_decorated

    return test_decorator
