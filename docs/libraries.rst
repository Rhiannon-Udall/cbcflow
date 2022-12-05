.. raw:: html

    <style> .red {color: red !important} </style>

.. role:: red

(proposal) Libraries in CBCFlow
===============================

Outline
-------
CBCFlow will use git repositories as its backend, structured as "libraries."
Each library consists of the metadata for some set of superevents, and a configuration file.
This configuration should describe rules for inclusion (e.g. a FAR threshold, or source classification),
as well as the relationship of the library to any potential parent library.
A parent library is one whose events are a superset of the events in this library.
:red:`EDITING NOTE: Should it be a strict superset? Would this potentially be an issue for lensing?``
This library is then downstream from the parent library, and should always pull updates from that library.
:red:`EDITING NOTE: Methods to do this have *not* been implemented yet.`
:red:`There should be methods to push and pull relevant events to/from the parent.`
:red:`The pull method should likely also be automated via a monitor.`
Notably, a parent-child relationship is distinct from cloning, which may also be used by individual users in relation to group level libraries.
This will form a hub-spoke (potentially recursively) structure to the overall collaboration libraries.

Example Usage
-------------
Consider an example BNS event S230401a, which is highly significant.
As per usual, GraceDB will automatically populate the page for this event, and followup will proceed accordingly.
Separately, the CBC group library will be running a GraceDB monitor to track GraceDB for updates.
At the next point in the monitor's cadence, it will identify S230401a and pull the information from GraceDB,
populating a default metadata json in the CBC group library.
A child parameter estimation library will also run a library monitor pulls this event automatically, and Asimov begins PE automatically as part of its own functionality.
When Asimov completes the PE, it will add the metadata for the results to the library, which is then pushed back to the CBC library.
:red:`EDITING NOTE: Would this be done automatically? Possibly Asimov triggers it rather than a cbcflow monitor?`
Once this occurs, a separate library monitor for the R&P child library pulls the updated metadata from the CBC library. 
The R&P library has another child library, specifically for BNS events, running its own library monitor which now pulls these updates.
R&P analysis is performed, and the metadata for this is added to the BNS library by a user
via typical git procedure (i.e. making a branch and submitting an MR).
Once this is done, the data gets pushed back to the R&P central library, and from there to the CBC library. 