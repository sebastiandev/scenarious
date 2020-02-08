import os
import re
from setuptools import setup, find_packages


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("^__version__ = ['\"]([^'\"]+)['\"]", init_py, re.MULTILINE).group(1)


setup(
    name='scenarious',
    setup_requires=[
        'six',
        'pyyaml==5.2',
        'Faker==2.0.3',
        'dateparser',
    ],
    install_requires=[
        'six',
        'pyyaml==5.2',
        'Faker==2.0.3',
        'dateparser',
    ],
    version=get_version('scenarious'),
    url='https://github.com/sebastiandev/scenarious',
    author='Sebastian Packmann',
    author_email='devsebas@gmail.com',
    description='A Tool for creating test scenarios',
    license='MIT',
    package_dir={
        'scenarious': 'scenarious',
        'scenarious.type_handlers': 'scenarious/type_handlers',
    },
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    test_suite='tests',
    keywords="unittest fixture scenario",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
