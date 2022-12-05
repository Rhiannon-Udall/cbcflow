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
Consider an example event S230401a, which is highly significant.
As per usual, GraceDB will automatically populate the page for this event, and followup will proceed accordingly.
Separately, the CBC group library will be running a monitor to track GraceDB for updates.
At the next point in its cadence, it will identify S230401a and pull the information from GraceDB,
populating a default metadata json in the CBC group library.

