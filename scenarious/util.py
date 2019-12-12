import os
import sys
import imp
import inspect
from collections import OrderedDict


class DictObject(dict):

    def __init__(self, *args, **kwargs):
        for a in args:
            if isinstance(a, (dict, OrderedDict)):
                kwargs.update(a)

        for k, v in kwargs.items():
            if isinstance(k, (dict, OrderedDict)):
                kwargs[k] = DictObject(**v)

            elif isinstance(v, (list, tuple)):
                kwargs[k] = [DictObject(**e) for e in v]

        super(DictObject, self).__init__(self, **kwargs)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError("%s doesn't have attribute '%s'" % (self.__class__.__name__, key))


def module_path(module_name, *args):
    if isinstance(module_name, str) and '.py' in module_name:
        path = os.path.realpath(module_name)

    else:
        module_name = module_name.__module__ if not isinstance(module_name, str) else module_name
        path = os.path.realpath(sys.modules[module_name].__file__)

    return path


def module_dir(module_name):
    return os.path.dirname(module_path(module_name))


class ModuleLoader(object):
    """
    Loads all modules inside a folder
    """
    group_path = None

    _modules = None

    @classmethod
    def is_allowed_file(cls, filename):
        return True

    @classmethod
    def is_allowed_class(cls, obj):
        raise NotImplementedError

    @classmethod
    def load(cls, paths=None, force=False):
        if cls._modules is None or force:
            cls._modules = []
            loaded_files = []
            _path = paths or cls.group_path
            _path = _path if type(_path) is list else [_path]

            for _p in _path:
                for path, dirs, subfiles in os.walk(_p):
                    for subfile in subfiles:
                        if not cls.is_allowed_file(subfile):
                            continue

                        module_name, module_ext = os.path.splitext(subfile)
                        module_ext = module_ext.lstrip(".")

                        if module_name != '__init__' and module_ext == 'py':
                            submodule_path = os.path.join(path, subfile)
                            if submodule_path not in loaded_files:
                                module = imp.load_source(module_name, submodule_path)

                                for member_name, obj in inspect.getmembers(module):
                                    if cls.is_allowed_class(obj):
                                        cls._modules.append(obj)

                                loaded_files.append(submodule_path)

        return cls._modules
