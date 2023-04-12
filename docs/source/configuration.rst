Configuration
=============

Environment
-----------

It is planned that CBCFlow will be available within the igwn environment - until this is true please see :doc:`development-setup` 
for the process of setting up an environment with CBCFlow.

Default Configuration
---------------------

CBCFlow has a user dependent default configuration, set in ``~/.cbcflow.cfg``. At present this will look like:

.. code-block::

    [cbcflow]
    gracedb_service_url=https://gracedb.ligo.org/api/
    library=/home/albert.einstein/cbcflow-library
    schema=None

Library and schema are optional arguments, setting the default library and schema.
The gracedb_service_url points to the instance of GraceDB which should be used.
If you would like to use a non-default configuration, you should format it like this, then point to it directly where applicable.

Argcomplete
-----------
``cbcflow`` uses `argcomplete <https://pypi.org/project/argcomplete/>`__
to help with setting arguments. There is a global completion setup (see
the documentation), but a fallback (often useful on clusters with
changing environments) is to register the executable directly. This can
be done by running


.. code-block::

   $ eval "$(register-python-argcomplete cbcflow_update_from_flags)"

Note, this command requires that you have installed ``argcomplete``.

Once initialised, you can tab complete to get help with setting elements
of the metadata. For example,

.. code-block::

   $ cbcflow_update_from_flags SXXYYZZabc --info-[TAB]

will either auto complete all the ``--info-`` options, or print a list
of available options.

Getting help
------------

For all cbcflow programs, one may run e.g.

.. code:: console

   $ cbcflow_update_from_flags --help

for help in how to use the program.

