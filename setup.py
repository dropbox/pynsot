#!/usr/bin/env python

from setuptools import find_packages, setup

execfile('pynsot/version.py')

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

kwargs = {
    'name': 'pynsot',
    'version': str(__version__),  # noqa
    'packages': find_packages(exclude=['tests']),
    'description': 'Python interface for Network Source of Truth (nsot)',
    'author': 'Jathan McCollum',
    'maintainer': 'Jathan McCollum',
    'author_email': 'jathan@dropbox.com',
    'maintainer_email': 'jathan@dropbox.com',
    'license': 'Apache',
    'install_requires': required,
    'url': 'https://github.com/dropbox/pynsot',
    'entry_points': """
        [console_scripts]
        nsot=pynsot.app:app
        snot=pynsot.app:app
    """,
    'classifiers': [
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
}

setup(**kwargs)
