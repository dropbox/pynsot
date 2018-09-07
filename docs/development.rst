Versioning
----------

We use `semantic versioning <http://semver.org>`_. Version numbers will
follow this format::

    {Major version}.{Minor version}.{Revision number}.{Build number (optional)}

Patch version numbers (0.0.x) are used for changes that are API compatible. You
should be able to upgrade between minor point releases without any other code
changes.

Minor version numbers (0.x.0) may include API changes, in line with the
:ref:`deprecation-policy`. You should read the release notes carefully before
upgrading between minor point releases.

Major version numbers (x.0.0) are reserved for substantial project milestones.

.. _release-process:

Release Process
---------------

When a new version is to be cut from the commits made on the ``develop``
branch, the following process should be followed. This is meant to be done by
project maintainers, who have push access to the parent repository.

#. Create a branch off of the ``develop`` branch called ``release-vX.Y.Z``
   where ``vX.Y.Z`` is the version you are releasing
#. Use ``bump.sh`` to update the version in ``pynsot/version.py`` and the
   Dockerfile. Example:

.. code-block:: bash

    $ ./bump.sh -v X.Y.Z

3. Update ``CHANGELOG.rst`` with what has changed since the last version. A
   one-line summary for each change is sufficient, and often the summary from
   each PR merge works.
#. Commit these changes to your branch.
#. Open a release Pull Request against the ``master`` branch
#. On GitHub, merge the release Pull Request into ``master``
#. Locally, merge the release branch into ``develop`` and push that ``develop``
   branch up
#. Switch to the ``master`` branch and pull the latest updates (with the PR you
   just merged)
#. Create a new git tag with this verison in the format of ``vX.Y.Z``
#. Push up the new tag

.. code-block:: bash

    # 'upstream' here is the name of the remote, it may also be 'origin'
    $ git push --tags upstream

11. Create a new package and push it up to PyPI (where ``{version}`` is the
    current release version):

.. code-block:: bash

    $ python setup.py sdist
    $ twine upload dist/pynsot-{version}.tar.gz

