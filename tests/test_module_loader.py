from scenarious.util import ModuleLoader


def test_module_loader_load_empty():
    actual = ModuleLoader.load(paths=[])
    expected = []
    assert actual == expected
    actual = ModuleLoader.load()
    assert actual == expected


def test_module_loader_invalid_paths():
    actual = ModuleLoader.load(paths=["./fixtures/test.yml", "test.txt", "test.py"])
    expected = []
    assert actual == expected


def test_module_loader_valid_paths():
    actual = ModuleLoader.load(paths=["test.py"])
    expected = []
    assert actual == expected