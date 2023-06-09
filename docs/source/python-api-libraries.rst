The ``LocalLibraryDatabase``
============================

The library object provides a number of attributes and methods which may prove useful, and 
you are encouraged to look through the API :doc:`api/cbcflow.database.LocalLibraryDatabase`.
However, for conciseness, this tutorial will focus on one important element: the use of git commands.
In the future, we will hopefully extend this to other topics. 

Using git with Libraries
------------------------

When automating scripts to interact with ``cbcflow``, it is very imporant to keep the library properly
up to date with the remote.
To this end, you will want to *always* pull from the remote before making automated updates, and then
push back your updates afterwards. 
We provide the methods required to do just that.
Prototypically, we start with:

.. code-block::

    >>> import cbcflow
    >>> library = cbcflow.database.LocalLibraryDatabase("/home/rhiannon.udall/meta-data/testing_libraries/cbcflow-tutorial-library")
    2023-06-09 13:53:18 CBCFlow INFO: Using cbc schema file /home/rhiannon.udall/meta-data/meta-data/src/cbcflow/schema/cbc-meta-data-v2.schema

as we did in the section on basics. 
Now, to pull updates for the library we can do:

.. code-block::

    >>> library.git_pull_from_remote(automated=True)

This will pull any updates from the remote for this library (naturally, you must have a remote "origin" configured).
The key word argument ``automated=True`` tells this library that if it finds a merge conflict in the process of pulling,
then it should abort the merge and then continue making edits.
This is desirable for automated pipelines, which could get stuck if they are not allowed to consistently update.
However, this conflict will need to be resolved before updates can be pushed back upstream, and so pipelines which
behave in this way should be semi-regularly monitored in case of merge conflicts.

Now, to edit meta-data for a robot we want to make one important change.
Starting as normal:

.. code-block::

    >>> update_dict = {"Info":{"Labels":["An example label"]}}
    >>> metadata.update(update_dict)
    >>> metadata["Info"]
    {'Labels': ['An example label'], 'SchemaVersion': 'v2', 'Notes': []}

We now want to write specifically to the main branch (since we don't want the robot to pile up other branches).
For this purpose, we can explicitly force the write to go to the main branch.
We will also want to provide some descriptive commit message:

.. code-block::

    >>> metadata.write_to_library(message="A pseudo-automated update", branch_name="main")
    2023-06-09 14:41:16 CBCFlow INFO: Super event: S230409lg, GPSTime=1365062495.091802, chirp_mass=1.43
    2023-06-09 14:41:16 CBCFlow INFO: Changes between loaded and current data:
    2023-06-09 14:41:16 CBCFlow INFO: {'Info': {'Labels': ['An example label']}}
    2023-06-09 14:41:16 CBCFlow INFO: Writing file /home/rhiannon.udall/meta-data/testing_libraries/cbcflow-tutorial-library/S230409lg-cbc-metadata.json
    2023-06-09 14:41:16 CBCFlow INFO: Commit explicitly made to main
    2023-06-09 14:41:17 CBCFlow INFO: Wrote commit a9ab94f353412eb83722ec5f4ed4d014685f547e

Once we have made the edits we wish to the metadata and written them to the library, we can push the changes back upstream:

.. code-block::

    >>> library.git_push_to_remote()

That's all!
Again, it's important that any automated processes doing this be monitored semi-regularly for merge conlicts.
Furthermore, note that this process is pushing to the main branch, which in the central library will be protected.
If you want your robot pushing directly to the central library, you should request an access token too let it push to this 
protected branch.
If you are pushing to a fork of the central library, then you may naturally implement protections in the way that you see fit.