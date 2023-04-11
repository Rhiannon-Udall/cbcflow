Command Line Interface
==========================

Pulling From GraceDB
--------------------

Pulling from GraceDB should be handled automatically by a central monitor.
However, if it is necessary to do manually (such as for testing), then it may be done with

.. code-block::

   $ cbcflow_pull SXXYYZZabc 


Updating Metadata Manually
--------------------------

Flag by Flag
^^^^^^^^^^^^

Updating from command line may be done in two ways. In the first, each flag corresponds to one change to an element. For example:

.. code-block::

   $ cbcflow_update_from_flags SXXYYZZabc --ParameterEstimation-Status-set "ongoing" \
   --ParameterEstimation-Analysts-add "Albert Einstein" \
   --ParameterEstimation-Reviewers-remove "Kip Thorne"

This will take three actions: the status (an element which is a string with a fixed set of possible values) will be set to ongoing (hence the set keyword).
The list of analysts (a list of strings) will have Albert Einstein added to it; if he is already there, this will add a second copy.
The list of reviewers (also a list of strings) will have Kip Thorne removed from it (assuming he is there, and if not nothing will happen). 

In some cases it may occur that you wish to edit the properties of an object instance. For example, there may be multiple ParameterEstimation-Results objects.
In this case, the UID should be used to designate which result will be modified. 
For example, to set the waveform used in the ParameterEstimation-Result "ProdF1", one would do:

.. code-block::

   $ cbcflow_update_from_flags SXXYYZZabc --ParameterEstimation-Results-UID-set ProdF1 \
   --ParameterEstimation-Results-WaveformApproximant-set IMRPhenomXPHM

In some cases (especially with TGR), this occurs in a nested fashion, in which case a UID is needed for each hierarchy which requires specification. For example

.. code-block::

   $ cbcflow_update_from_flags SXXYYZZabc --TestingGR-IMRCTAnalyses-UID-set IMRCT1 \
   --TestingGR-IMRCTAnalyses-SafeLowerMassRatio-set 2 \
   --TestingGR-IMRCTAnalyses-Results-UID-set ProdF1 \
   --TestingGR-IMRCTAnalyses-Results-WaveformApproximant IMRPhenomXPHM

Importantly, this means that only one UID may be modified at a time, so if e.g. you want to modify ProdF2, that must be a separate call.

From a File
^^^^^^^^^^^

The above method is good for when you only want to change a few elements, and they are relatively easy to access.
However, if you want to make changes in bulk, it may be more useful to write out a yaml or json containing your updates.
Once you have such a file, then you can do:

.. code-block::

   $ cbcflow_from_file SXXYYZZabc my_update.yaml

For example, to implement the (most of) the first case above, ``my_update.yaml`` would look like

.. code-block::

   ParameterEstimation
     Status: ongoing
     Analysts: 
     - Albert Einstein

To do the removal, it is necessary to make a separate "negative image" file, which would look like 

.. code-block::

   ParameterEstimation
     Reviewers
     - Kip Thorne

and then pass this with

.. code-block::
   
   $ cbcflow_from_file SXXYYZZabc my_removal.yaml --removal-file
      
That is, the flag removal file tells cbcflow to remove all elements presented in the update file. 
Note that removal is only meaningful for arrays of primitive types, such as strings, numbers, and the like.
Once an object (for example a PE result) has been added, it may not be removed except by hand
(reflective of the fact that such a thing *shouldn't* be removed in the logistical sense).

The convenience of this method is heightened for cases where one wishes to edit multiple UID referenced objects at once.
For example, to do the second case from the command line above, one would make this yaml:

.. code-block::

   ParameterEstimation
     Result
     - UID: ProdF1
       WaveformApproximant: IMRPhenomXPHM

and the third case above would be 

.. code-block::

   TestingGR
     IMRCTAnalyses
     - UID: IMRCT1
       SafeLowerMassRatio: 2
       Results
       - UID: ProdF1
         WaveformApproximant: IMRPhenomXPHM

However, now both of these may be extended:

.. code-block::

   ParameterEstimation
     Result
     - UID: ProdF1
       WaveformApproximant: IMRPhenomXPHM
     - UID: ProdF2
       WaveformApproximant: SEOBNRv4PHM

and 

.. code-block::

   TestingGR
     IMRCTAnalyses
     - UID: IMRCT1
       SafeLowerMassRatio: 2
       Results
       - UID: ProdF1
         WaveformApproximant: IMRPhenomXPHM
       - UID: ProdF2
         WaveformApproximant: SEOBNRv4PHM
     - UID: IMRCT2
       SafeLowerMassRatio: 3
       Results
       - UID: ProdF1
         WaveformApproximant: SEOBNRv4PHM
       - UID: ProdF2
         WaveformApproximant: IMRPhenomXPHM

will both work correctly. Thus if you want to edit many such objects simultaneously, it is advisable to use the ``cbcflow_from_file`` method. 
This also works equivalently for JSON files of the appropriate structure.
Finally, as described in :doc:`usage-for-scripting`, one may use the API to edit metadata in a manner analogous to this,
using JSONs instantiated in python. 