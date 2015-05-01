"""
This is a pseudo module that allows you to proxy imports. This lets you
import dependencies in the form `from .vendor import requests`. We provide
a hook through the environment variable _PYNSOT_PYTHONPATH to override
the path for `pynsot` dependencies, otherwise it uses sys.path by default.

There is a limitation with dependencies that use absolute imports in their
packages as they will not be imported under the pynsot.vendor namespace.
"""

import sys
import os

# os.path doesn't import cleanly with this system from dependencies.
# Manually import so that it's available in the sys.modules cache.
import os.path


def get_path():
    env = os.environ.get("_PYNSOT_PYTHONPATH")
    if env:
        return env.split(":")
    return sys.path


__path__ = get_path()
