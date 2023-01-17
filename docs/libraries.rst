.. raw:: html

    <style> .red {color: red !important} </style>

.. role:: red

Libraries in CBCFlow
===============================

Outline
-------
CBCFlow will use git repositories as its backend, structured as "libraries."
Each library consists of the metadata for some set of superevents, and a configuration file.
One central repository will be maintained by the CBC group broadly,
and this will pull default information directly from GraceDB via monitor.
Sub-groups may maintain their own forks of this library.
These forks would have different configurations, but the same superevents.
These different configurations will be used to automatically populate indices describing events which meet configuration criteria.
Sub-group forks can run monitors to automatically pull from their upstream,
but pushes back to the CBC central library will be manually triggered by responsible parties within the sub-group.
Management of sub-group repositories would be a matter left to respective sub-groups.

Example Usage
-------------
Consider an example BNS event S230401a, which is highly significant.
As per usual, GraceDB will automatically populate the page for this event.

.. image:: /libraries_images/part_1.png
  :width: 1200

The CBC central library monitor will pick this event up, and populate the CBC library with defaults. 


.. image:: /libraries_images/part_2.png
  :width: 1200


Detchar followup will proceed independently,
and once recommended settings are generating they will be automatically pushed to the CBC library. 

.. image:: /libraries_images/part_3.png
  :width: 1200

Asimov will read in detchar recommendations and produce PE automatically,
then push the metadata of these results back to the CBC library. 

.. image:: /libraries_images/part_4.png
  :width: 1200

Once this occurs, a separate library monitor for the R&P child library pulls the updated metadata from the CBC library.
Because this event satisfies inclusion criteria for R&P, it is automatically added to the library index. 

.. image:: /libraries_images/part_5.png
  :width: 1200

The R&P library has child libraries for BNS and BBH events respectively,
each running its own library monitor which now pulls these updates.
The BNS monitor updates that child repository's index,
while the BBH monitor excludes it from its own index based on source classification. 

.. image:: /libraries_images/part_6.png
  :width: 1200

R&P analysis is performed, and the metadata for this is added to the BNS library by a user
via typical git procedure (i.e. making a branch and submitting an MR).

.. image:: /libraries_images/part_7.png
  :width: 1200

Once this is done, the data gets pushed back to the R&P central library, and from there to the CBC library. 

.. image:: /libraries_images/part_8.png
  :width: 1200
