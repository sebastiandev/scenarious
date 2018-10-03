import unittest
from scenarious.testing import scenario, ScenariousBaseTest
from tests.test_scenarious import ActorTypeHandler


class ScenariousFixtureWithTestClassTest(unittest.TestCase, ScenariousBaseTest):

    @scenario("""
      actors:
        - name: test
          age: 20

        - id: 2
          name: test2
          age: 22
    """, handlers=[ActorTypeHandler])
    def test_fixture_simple(self):
        assert 2 == len(self.actors)
        assert "test" == self.actors[0].name
        assert "test2" == self.actors[1].name

    scenario_a = """
      actors:
        - name: test
          age: 20
    """
    scenario_b = """
      actors:
        - id: 2
          name: test2
          age: 22
    """

    @scenario(scenario_a, scenario_b, handlers=[ActorTypeHandler])
    def test_fixture_with_merged_scenarios(self):
        assert 2 == len(self.actors), self.actors
        assert "test" == self.actors[0].name
        assert "test2" == self.actors[1].name


class ScenariousFixtureWithoutTestClassTest(unittest.TestCase):

    @scenario("""
      actors:
        - name: test
          age: 20

        - id: 2
          name: test2
          age: 22
    """, handlers=[ActorTypeHandler])
    def test_fixture(self, scenario):
        assert 2 == len(scenario.actors)
        assert "test" == scenario.actors[0].name
        assert "test2" == scenario.actors[1].name
