(proposal) GWOSC Integration 
============================
An important feature of CBCFlow will be a web portal
which allows visualization of library contents easily,
without having to manually read the json files.
Simultaneously, a known development goal in the medium term
would be to create standard conversion methods from CBCFlow meta-data
into GWOSC event portal data, for public release with the catalogs.
These two goals could be very well meshed if we implement these conversion
methods promptly, and use them to create internal GWOSC event portals.
Doing so would also have the advantage of allowing the paper writing teams
to work from a good approximation of the final product, rather than producing
the event catalogs and catalog papers separately.

Implementation Details
----------------------
A GWOSC server may either be stood up or repurposed, and loaded with the event portal backend.
Separate sub-group / paper libraries may be represented within this, using CBCFlow configuration 
tools to guide inclusion.

Forward Planning
----------------
Before integration can proceed, a number of pre-requisites must be fulfilled on the CBCFlow side:

#. A standard test library, with representative contents, and a representative sub-group fork of this library

#. Finalization of usage instructions, and stabilization of core tools

Integration will consist of:

#. Creating conversion scripts from CBCFlow fields to the GWOSC database

#. Determining the server upon which the portal will be hosted

#. Expanding access scripts to allow fetching of data not directly stored in CBCFlow (e.g. CIs of posteriors)