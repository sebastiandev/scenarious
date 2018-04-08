import unittest
from scenarious.testing import scenario, ScenariousBaseTest
from tests.test_scenarious import ActorTypeHandler


class ScenariousFixtureWithTestClassTest(ScenariousBaseTest):

    @scenario("""
      actors:
        - name: test
          age: 20

        - id: 2
          name: test2
          age: 22
    """, handlers=[ActorTypeHandler])
    def test_fixture(self):
        assert 2 == len(self.actors)
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
