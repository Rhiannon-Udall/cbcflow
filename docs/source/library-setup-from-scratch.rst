Making Your Own Library
=======================
At its core, a library in CBCFlow is a git repository, so the first step is to setup such a git repository.

Typically, one will be able to fork the main CBC library. This has not yet been setup, and these documents will be updated to include the link once it is available.

The ``library.cfg`` file
------------------------

Once a repository has been setup, the other step is to setup the configuration file. Currently, this should be named ``library.cfg``.
Notably, this means that this configuration file should vary between forks and source repositories.
Prototypically this looks like this:

.. code-block::

    [Library Info]
    library-name=LVK-demonstration-library

    [Events]
    far-threshold=1e-30
    created-since=2023-03-01
    created-before=2023-04-01
    snames-to-include=[]
    snames-to-exclude=[]

    [Monitor]
    parent=gracedb

The library-name designates the name given to this library configuration file.
Currently this principally serves to name the index file.

The Events properties designate the filtering parameters for the library.
The far-threshold dictates the maximum FAR (per GraceDB definition) of events which may be included in the library.
The parameters created-since and created-before determine the dates of events which may be included in this library.
The parameters snames-to-include and snames-to-exclude allow explicit inclusion and exclusion of specific events, as designated by sname.
Inclusion takes two forms: if the library pulls from GraceDB (see below), it decides the parameters of the query, and in any circumstance it will decide inclusion rules for the index.
The index is a file containing all events satisfying the configuration inclusion rules, and when they were last updated.

Finally, the parent parameter sets the parent of the repository - either GraceDB or another repository. 
This will then set how pulling from the parent works - currently only pulling from GraceDB has been implemented.

Merge Configuration
-------------------

As discussed :doc:`cbcflow-git-merging`, ``cbcflow`` requires special merging logic to handle json files correctly.
This must be configured on a local basis for each library, as discussed in :doc:`local-library-copy-setup`.
Unlike that case though, we will need to write the setup scripts ourselves, since this is a new git repository.
Two things need to be done: ``.git/config`` has to be added to include our new merge strategy, and ``.gitattributes`` needs to point to this strategy for ``*-cbc-metadata.json`` files.
The second is easier, so we'll start with that.
Simply create a file ``.gitattributes`` in the root directory of the repository, with these contents:

.. code-block::

    *-cbc-metadata.json merge=json_merge

That's it, easy enough.
The next step is a little more complicated, but not by much. 
We write two files, the first is the definition of the strategy, into a file called ``.gitconfig`` which looks like this:

.. code-block::

    [merge "json_merge"]
        name = Our custom way of merging cbc-metadata.json files
        driver = cbcflow_git_merge %O %A %B
        recursive = binary

The other file we'll call ``setup-cbcflow-merge-strategy.sh``, and it's just a simple bash script:

.. code-block::

    #!/bin/bash
    cat .gitconfig >> .git/config

This is the script you run to append the strategy to the end of ``.git/config``, a necessary step since that file should not be tracked, and hence must be edited locally.
Credit should be given to https://github.com/Praqma/git-merge-driver for describing this approach clearly.