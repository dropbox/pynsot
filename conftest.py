# Prvent import of django settings when using python 3.
# This can be removed once NSOT supports python 3.
import sys
import os

if sys.version_info[0] < 3:
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.nsot_settings"
