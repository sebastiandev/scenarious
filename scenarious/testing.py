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
    def build_scenario(cls, *data_streams, **kwargs):
        handlers = kwargs.pop('handlers', None)
        scenario_class = kwargs.pop('scenario_class', None) or cls.scenario_handler

        scenario = None
        data_streams = data_streams or [{}]

        for data_stream in data_streams:
            data = StringIO(data_stream) if type(data_stream) is str else data_stream

            if not scenario:
                scenario = scenario_class.load(data, handlers or cls.type_handler_loader.load())
            else:
                scenario.update(data)

        return scenario

    def create_scenario(self, *data_streams, **kwargs):
        self._scenario = self.build_scenario(*data_streams, **kwargs)

    def __getattr__(self, item):
        if '_scenario' not in self.__dict__:
            raise AttributeError("ScenariousBaseTest doesnt have attribute {}".format(item))

        if hasattr(self._scenario, item):
            r = getattr(self._scenario, item)
            return r if item.endswith('s') else r[0]
        else:
            raise AttributeError("ScenariousBaseTest Scenario doesnt have attribute {}(s)".format(item))


def scenario(*data_streams, **kwargs):
    handlers = kwargs.pop('handlers', None)
    scenario_class = kwargs.pop('scenario_class', None)

    def test_decorator(f):
        @wraps(f)
        def test_decorated(self, *args, **kwargs):
            # TODO: If we want to have a base scenario defined in the setUp
            # we might want to add the data from data_stream into that scenario
            # instead of just replace it

            if isinstance(self, ScenariousBaseTest):
                self.create_scenario(*data_streams, handlers=handlers)
                f(self, *args, **kwargs)
            else:
                # If not using ScenariousBaseTest, then inject scenario as a test parameter
                kwargs['scenario'] = ScenariousBaseTest.build_scenario(*data_streams,
                                                                       handlers=handlers,
                                                                       scenario_class=scenario_class)
                f(self, *args, **kwargs)

        return test_decorated

    return test_decorator
