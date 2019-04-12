# Scenarious   [![Build Status](https://travis-ci.org/sebastiandev/scenarious.svg?branch=development)](https://travis-ci.org/sebastiandev/scenarious)
A Tool for creating testing scenarios

Having fixtures or test scenarios defined in re-usable, combinable, shareable ways is a good thing as well as having them in a format that doesnt require coding habilities to understand them. Thats what scenarious offers

## Install
```pip install scenarious```

### Cutting edge 
```pip install -e git+https://github.com/sebastiandev/scenarious@development```

### Python 2.7
```pip install -e git+https://github.com/sebastiandev/scenarious@python-2.7```


## Getting Started

We can create a yaml file that will describe our data or we can create it as a StringIO in your unit test. Both approaches will look the same, we need to define our data types and start specifying our test scenario:

```yaml
actors:
  - name: John Travolta
    age: 64
    
  - name: Brad Pitt
    age: 55
    
  - name: Edward Norton
    age: 49
    
  - name: Hugh Jackman
    age: 50

genres:
  - name: Action
  - name: Drama
  
movies:
  - title: Pulp Fiction
    year: 1994
    genre: $genre_1
    actors: 
      - $actor_1
    
      
  - title: Fight Club
    year: 1999
    genre: $genre_1
    actors: 
      - $actor_2
      - $actor_3
      
  - title: The Fountain
    year: 2006
    genre: $genre_2
    actors: 
      - $actor_4
```      

That's it, and is quite self descriptive, but there are some tricks there...

#### Relationships or References
First thing one notices is that there seem to be some sort of relationship between the types, and that happens pretty often when modelling entities, in **scenarious** we repsent references like this:
```${entity_type}_{id_or_alias}```

For the case of the movies
```yaml
movies:
  - title: Pulp Fiction
    year: 1994
    genre: $genre_1
    actors: 
      - $actor_1
```

```$actor_1``` is referencing the actor with id 1. If we didnt define an id on the actors, then the id is automatically generated by the order in which they are processed. So the actor 1 is *John Travolta*

When assigning values to attributes we could want to assign the value of an existing entity, so instead of referencing the entire entity, we'd just want the entitie's attribute. So we can use the referencing and add the attribute we want:

```${entity_typ}]_{id_or_alias}.{attribute_name}```

There's no limit in the depth of *hops* or relationship chain, as long as they are defined in your models then they can be navigated and referenced.


#### Type Handlers

Each model that you use/define in a scenario needs to have a TypeHandler which is the resposible of creating the actual entity in the database, passing all the required attributes, applying defaults and defining required fields to be defined by the user, if any.


```python
class MovieHandler(TypeHandler):

    __type_name__ = 'movie'
    __requires__ = ['title', 'genre', 'actors']

    year = lambda: faker.year()
    director = lambda: faker.random_sample(['Scorsese', 'Tarantino', 'Spielberg', 'Ridley Scott'], 1)
    studio = lambda: faker.random_sample(['Universal', 'MGM', 'DreamWorks', 'Disney'], 1)
    budget = lambda: Decimal(faker.random_int(10000, 50000000))
    
```

Here you can see that movie required the user to define the title, genre and actors fields, the rest are all randomly generated using the faker library

##### SQLAlchemy
When using sqlalchemy the type handler definition needs to know the model you are referring to in the schema, so we need to use the *SQLALchemyTypeHandler* and expect models to have a ```.create(**kwargs)``` method.

```python
from scenarious.sql_alchemy import SQLALchemyTypeHandler


class MovieHandler(SQLALchemyTypeHandler):

    __type_name__ = 'movie'
    __model__ = Movie  # what ever model you have defined for your movies
    __requires__ = ['title', 'genre', 'actors']

    year = lambda: faker.year()
    director = lambda: faker.random_sample(['Scorsese', 'Tarantino', 'Spielberg', 'Ridley Scott'], 1)
    studio = lambda: faker.random_sample(['Universal', 'MGM', 'DreamWorks', 'Disney'], 1)
    budget = lambda: Decimal(faker.random_int(10000, 50000000))
```

If there's some custom logic needed for the entity creation, you can extend/override the ```._do_create(self, data)``` method as well as the constructor


#### Loading a scenario

Now we have to actually tell scenarious to load this scenario into our database

```python
from StringIO import StringIO
from scenarious import Scenario, TypeHandler

class MovieHandler(TypeHandler):

    __type_name__ = 'movie'
    __requires__ = ['title', 'genre', 'actors']

    year = lambda: faker.year()
    director = lambda: faker.random_sample(['Scorsese', 'Tarantino', 'Spielberg', 'Ridley Scott'], 1)
    studio = lambda: faker.random_sample(['Universal', 'MGM', 'DreamWorks', 'Disney'], 1)
    budget = lambda: Decimal(faker.random_int(10000, 50000000))


class ActorHandler(TypeHandler):

    __type_name__ = 'actor'
    __requires__ = ['name']

    age = lambda: faker.random_int(20, 80)


class GenreHandler(TypeHandler):

    __type_name__ = 'genre'
    __requires__ = ['title']


scenario = Scenario.load(StringIO("""
actors:
  - name: John Travolta
    age: 64
    
  - name: Brad Pitt
    age: 55
    
  - name: Edward Norton
    age: 49
    
  - name: Huge Jackman
    age: 50

genres:
  - name: Action
  - name: Drama
  
movies:
  - title: Pulp Fiction
    year: 1994
    genre: $genre_1
    actors: 
      - $actor_1
    
      
  - title: Fight Club
    year: 1999
    genre: $genre_1
    actors: 
      - $actor_2
      - $actor_3
      
  - title: The Fountain
    year: 2006
    genre: $genre_2
    actors: 
      - $actor_4
"""), type_handlers=[MovieTypeHandler, ActorTypeHandler, GenreTypeHandler)
```

And you are done, the database already has the actors, genres and movies. You can now start testing your app.

#### Type Handler Loading
As an application grows, you will probably have many type handlers and having to manually specify each one of them when loading the scenario is a bit verbose. So that why a *TypeHandlerLoader* exists. 
There are two ways of loading you handlers

```python
from scenarious import TypeHandlerLoader
from scenarious.utils import module_dir


# Option 1
handlers = TypeHandlerLoader.load('/some/path/to/your/app')


# Option 2
class CustomTypeHandlerLoader(TypeHandlerLoader):
    group_path = module_dir(__file__)  # if they are all in the same folder


# Option 3
class CustomTypeHandlerLoader(TypeHandlerLoader):
    group_path = ['/some/path/', '/another/path']  # if you have them in different places
    
    
handlers = CustomTypeHandlerLoader.load()
```


#### Unit Testing
In order to make scenarious even easier to use for testing, there's a base class for your tests that provides with
shortcuts to initialize and create scenarios, as well as a decorator to create scenarios for specific test methods

##### Base Test Class
There's the **ScenariousBaseTest** class that provides a few shortcuts for creating the scenarios and accesing the entities

```python
from unittest import BaseTest
from scenarious import testing, Scenario

class CustomTest(BaseTest, testing.ScenariousBaseTest):

    scenario_handler = Scenario  # you can specify you own class that extends Scenario here to be used in the tests
    type_handler_loader = CustomTypeHandlerLoader  # the custom loader we created above

    def setUp(self):
        self.create_scenario("""
        actors:
          - name: John Travolta
            alias: John
            age: 64
    
          - name: Brad Pitt
            alias: Brad
            age: 55
    
          - name: Edward Norton
            alias: Ed
            age: 49
        """)
    
    def test_actors(self):
        assert 3 == self.actors  # we are accessing all the actors
        assert 'Edward Norton' == self.actors[2].name  # we access by order of definition
        assert 'Edward Norton' == self._scenario.by_id('actor', 'Ed').name  # we access by alias
```

##### Decorator
There's also a decorator to be able to create specific scenarios for single test methods. The decorator
can be used with a subclass of ScenariousBaseTest and without it, but in that case you will need to
specify which scenario class to use and the type handlers

```python
from unittest import BaseTest
from scenarious import testing, Scenario

class CustomTest(BaseTest, testing.ScenariousBaseTest):

    scenario_handler = Scenario  # you can specify you own class that extends Scenario here to be used in the tests
    type_handler_loader = CustomTypeHandlerLoader  # the custom loader we created above

    @testing.scenario("""
    actors:
      - name: John Travolta
        alias: John
        age: 66
    
      - name: Brad Pitt
        alias: Brad
        age: 55
    
      - name: Edward Norton
        alias: Ed
        age: 51
    """)
    def test_actors_with_decorator(self):
        assert 3 == self.actors  # we are accessing all the actors
        assert 'Edward Norton' == self.actors[2].name  # we access by order of definition
        assert 'Edward Norton' == self.by_id('actor', 'Ed').name  # we access by alias

class PlainTest(BaseTest):

    @testing.scenario("""
    actors:
      - name: John Travolta
        alias: John
        age: 66
    
      - name: Brad Pitt
        alias: Brad
        age: 55
    
      - name: Edward Norton
        alias: Ed
        age: 51
    """, scenario_class=Scenario, handlers=[ActorTypeHandler])
    def test_actors_with_decorator(self, scenario):
        # If we are not subclassing ScenariousBaseTest, then we need to specidy 
        # the Scenario class we wantn to use as well as the handlers        
        assert 3 == scenario.actors  # we are accessing all the actors
        assert 'Edward Norton' == scenario.actors[2].name  # we access by order of definition
        assert 'Edward Norton' == scenario.by_id('actor', 'Ed').name  # we access by alias
```
