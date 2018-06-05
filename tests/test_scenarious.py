import unittest
from uuid import uuid4
from random import randint

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from scenarious.util import DictObject
from scenarious.type_handlers.base import faker, TypeHandlerException
from scenarious import Scenario, TypeHandler, ScenariousException


class BaseTestTypeHandler(TypeHandler):

    @classmethod
    def _do_create(cls, data):
        data['id'] = str(uuid4())
        return DictObject(**data)


class ActorTypeHandler(BaseTestTypeHandler):

    __type_name__ = 'actor'
    __requires__ = ['name']

    age = lambda: randint(18, 80)


class FilmTypeHandler(BaseTestTypeHandler):

    __requires__ = ['title', 'genre']

    actor = None


class MovieTypeHandler(FilmTypeHandler):

    __type_name__ = 'movie'
    __requires__ = ['year']


class TVShowTypeHandler(FilmTypeHandler):
    __type_name__ = 'tvshow'
    __requires__ = ['seasons']


class GenreTypeHandler(BaseTestTypeHandler):
    __type_name__ = 'genre'

    name = lambda: faker.random_sample(['drama', 'comedy', 'action'], length=1)[0]


class ScenariousTest(unittest.TestCase):

    def test_load_type(self):
        s = Scenario.load(StringIO("""
        actors:
          - name: test
            age: 20

        movies:
          - title: test movie
            genre: drama
            year: 2018
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert s.actors
        assert 1 == len(s.actors)
        assert 'test' == s.actors[0].name
        assert 20 == s.actors[0].age

        assert s.movies
        assert 1 == len(s.movies)
        assert 'test movie' == s.movies[0].title
        assert 'drama' == s.movies[0].genre

    def test_custom_ids(self):
        s = Scenario.load(StringIO("""
        actors:
          - id: 1
            name: test1
            age: 20

          - id: 3
            name: test2
            age: 22
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert s.actors
        assert 2 == len(s.actors)

        assert 'test1' == s.by_id('actors', 1).name
        assert 'test2' == s.by_id('actors', 3).name

    def test_alias_objects(self):
        s = Scenario.load(StringIO("""
        actors:
          - id: 1
            _alias: test1
            name: test1
            age: 20

          - id: 3
            name: test2
            age: 22
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert s.actors
        assert 2 == len(s.actors)

        assert 'test1' == s.by_id('actors', 'test1').name
        assert not s.by_id('actors', 'test2')  # id:3 has no alias

    def test_fail_with_duplicate_alias(self):
        scene = StringIO("""
        actors:
          - id: 1
            _alias: xx
            name: test1
            age: 20

          - id: 3
            _alias: xx
            name: test2
            age: 22
        """)
        self.assertRaises(ScenariousException, Scenario.load, scene, type_handlers=[ActorTypeHandler, MovieTypeHandler])

    def test_mix_auto_generated_and_custom_ids(self):
        s = Scenario.load(StringIO("""
        actors:
          - name: test1
            age: 20

          - name: test2
            age: 22

          - id: 1
            name: test3
            age: 33
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert s.actors
        assert 3 == len(s.actors)

        assert 'test3' == s.by_id('actors', 1).name
        assert 'test2' == s.by_id('actors', 2).name
        # should've been forced to relocate because of test33 having _id:1
        assert 'test1' == s.by_id('actors', 3).name

    def test_get_object_by_id(self):
        s = Scenario.load(StringIO("""
        actors:
          - name: test
            age: 20

          - id: 2
            name: test2
            age: 22

        movies:
          - title: test movie 1
            genre: drama
            actor: $actor_1
            year: 2018
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert 20 == s.by_id('actors', 1).age
        assert "test" == s.by_id('actors', 1).name
        assert 22 == s.by_id('actors', 2).age
        assert "test2" == s.by_id('actors', 2).name

        assert "test movie 1" == s.by_id('movies', 1).title
        assert not s.by_id('movies', 99)

    def test_reference_objects(self):
        s = Scenario.load(StringIO("""
        actors:
          - name: test
            age: 20

          - id: 2
            name: test2
            age: 22

        movies:
          - title: test movie 1
            genre: drama
            actor: $actor_1
            year: 2018

          - title: test movie 2
            genre: action
            actor: $actor_2
            year: 2018
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert s.actors
        assert s.movies
        assert 'test' == s.by_id('movies', 1).actor.name
        assert 'test2' == s.by_id('movies', 2).actor.name

    def test_reference_object_by_alias(self):
        s = Scenario.load(StringIO("""
        actors:
          - _alias: test1
            name: test
            age: 20

          - _alias: test2
            id: 2
            name: test2
            age: 22

        movies:
          - title: test movie 1
            genre: drama
            actor: $actor_test1
            year: 2018

          - title: test movie 2
            genre: action
            actor: $actor_test2
            year: 2018
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        assert s.actors
        assert s.movies
        assert 'test' == s.by_id('movies', 1).actor.name
        assert 'test2' == s.by_id('movies', 2).actor.name

    def test_load_defaults(self):
        config = StringIO("""
        genres: 2
        """)

        scenario = Scenario.load(config, [GenreTypeHandler])

        assert 2 == len(scenario.genres)

        assert scenario.genres[0]
        assert scenario.genres[1]
        assert scenario.genres[0].id != scenario.genres[1].id
        assert scenario.genres[0].name in ['drama', 'comedy', 'action']

    def test_load_type_missing_required_field(self):
        config = StringIO("""
        actors: 1
        """)

        scenario = None
        try:
            scenario = Scenario.load(config, [ActorTypeHandler])

        except Exception as e:
            assert isinstance(e, TypeHandlerException)

        assert not scenario

    def test_add_objects_to_scenario(self):
        s = Scenario.load(StringIO("""
        actors:
          - name: test
            age: 20

          - id: 2
            name: test2
            age: 22

        movies:
          - title: test movie 1
            genre: drama
            actor: $actor_1
            year: 2018

          - title: test movie 2
            genre: action
            actor: $actor_2
            year: 2018
        """), type_handlers=[ActorTypeHandler, MovieTypeHandler])

        s.add_actor(dict(name="New actor", age=33))
        s.add_movie(dict(title="New movie", genre="thriller", actor=s.actors[0], year=2018))

        assert 3 == len(s.actors)
        assert 3 == len(s.movies)


