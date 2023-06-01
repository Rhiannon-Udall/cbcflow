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
   # Set the library to use by default
   # In typical use this is likely a result of git cloning the O4a library:
   # https://git.ligo.org/cbc/projects/cbc-workflow-o4a
   # For command line calls you can always set a non-default library to use with the flag
   # --library path/to/library
   library=/home/albert.einstein/sub/directory/path/cbc-workflow-o4a

   # The gracedb service url to use: this should be set as below
   # However, in most cases it will not prove necessary
   # For the average user
   gracedb_service_url=https://gracedb.ligo.org/api/

   # Optionally you may point to a non-standard meta-data schema
   # Take caution in doing so!
   # This would take the form of
   # schema=/path/to/schema/file

   # You may also point to a non-standard index schema
   # This will be exceedingly uncommon, since the standard index schema is already quite flexible
   # However, it is included for completeness
   # This would take the form of
   # index-schema=/path/to/index/schema/file

All of these arguments are, strictly speaking optional.
It is recommended to set a default library, strictly from an ergonomic perspective, 
but the average user may comfortably choose not to set the other fields 
(or, for ease of use, just copy the above and leave them unchanged).

If you want to use a specific configuration for, e.g. a monitor,
then this may be written and pointed to by the relevant program directly. 

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

   $ cbcflow_update_from_flags SXXYYZZabc --Info-[TAB]

will either auto complete all the ``--Info-`` options, or print a list
of available options.

Getting help
------------

For all cbcflow programs, one may run e.g.

.. code:: console

   $ cbcflow_update_from_flags --help

for help in how to use the program.

