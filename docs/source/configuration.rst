Configuration
=============
It is planned that CBCFlow will be available within the igwn environment - until this is true please see :doc:`development-setup` 
for the process of setting up an environment with CBCFlow.

CBCFlow has a user dependent default configuration, set in ``~/.cbcflow.cfg``. At present this will look like:

.. code-block::

    [cbcflow]
    gracedb_service_url=https://gracedb.ligo.org/api/
    library=/home/albert.einstein/cbcflow-library
    schema=None

Library and schema are optional arguments, setting the default library and schema.
The gracedb_service_url points to the instance of GraceDB which should be used.