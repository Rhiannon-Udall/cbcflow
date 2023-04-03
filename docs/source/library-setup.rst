Library Configuration
=====================
At its core, a library in CBCFlow is a git repository, so the first step is to setup such a git repository.

Typically, one will be able to fork the main CBC library. This has not yet been setup, and these documents will be updated to include the link once it is available.

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

