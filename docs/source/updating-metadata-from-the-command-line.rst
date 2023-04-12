Command Line Interface
==========================

For many users, the main tool for interacting with ``cbcflow`` metadata are the suite of command line tools.
These allow you to:
* Print the contents of a metadata file
* Pull GraceDB information into a metadata file
* Update a metadata file using a series of flags
* Update a metadata file by writing a file containing many changes
This documentation will go over how to use each of those, and also provide an introduction to updating metadata in general.

This page assumes that you have read :doc:`what-is-metadata` and :doc:`reading-the-schema` already -
if you haven't it is strongly encouraged that you do so first.

The Tutorial Library
--------------------

If you would like to follow along with this documentation, you can check out the tutorial library at 
https://git.ligo.org/rhiannon.udall/cbcflow-tutorial-library.
To follow along, fork this library and clone it, then configure it as your default library.
If you aren't sure how to configure this as a default, check out :doc:`configuration`.

This library contains a few events from April 9th, as well as some other example contents.

Printing File Contents
----------------------

The simplest action one can take with metadata is to view it's contents. 
To do this for an event in our tutorial library, simply do:

.. code-block::

  cbcflow_print S230409dx

This will print out the contents of this superevent.
If you scroll up to read these, you will notice that a few fields have been given example values.
You can also see that the GraceDB data has been pre-populated.

Pulling From GraceDB
--------------------

In most cases, pulling directly from GraceDB should not be necessary, because the library will be kept up to date with GraceDB by a monitor.
These monitors follow configuration set in the library (see :doc:`library-setup` for details) - in our case the configuration targets events with FAR<1e-30 which occurred in the MDC on April 9th.
Let's grab a new event, ``S230410x``, from GraceDB:

.. code-block::

   $ cbcflow_pull S230410x

Now, you can print the contents as above, and see that the GraceDB section has quite a bit of content filled in!

Updating Metadata
-----------------

Figuring Out What to Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The biggest challenge in figuring out how to update metadata, is figuring out what field you're actually trying to change!
For this reason, unless you already know what you want to edit (probably by having made the same edit a dozen times before),
you should probably open :doc:`schema-visualization` and keep it close at hand.

Now, let's consider some examples. 
Firstly, say you have participated in parameter estimation for some event, and want to mark down that you were one of the analysts.
What should we try to modify?
Well, first we go to the schema visualization, and see the over-arching section headers.
We know we are changing something about parameter estimation, and there is a section header ``ParameterEstimation``, so we can expand that one out.
There are a lot of properties under this header, but one seems appropriate - ``Analysts`` certainly seems like what we are looking for.
To make sure, we can expand it out, and read the description: it says that it is an array, described as "The names of all analysts involved", so this is probably what should be modified!
To describe the field we've just chosen, let's write it like this: ``ParameterEstimation-Analysts``.
That corresponds to the the field ``Analysts``, in the field ``ParameterEstimation`` - an important distinction since ``Analysts`` is a field that also occurs in other places!
Remember this notation, because it will come in handy shortly.

Now, lets say we want to do something a bit more complicated. 
Having done a parameter estimation analysis, we want to record some information about that analysis.
Looking back at the ``ParameterEstimation`` section, we see there are a couple things with "Result" in their name.
However, checking out the contents of ``IllustrativeResult`` and ``SkymapReleaseResult`` we see they are both just strings that name a certain result to use in some situation, which isn't quite right.
In contrast, ``Results`` is a collection of ``PEResult`` objects, which seems more like what we are looking for.
Let's take a moment to note that our path *so far* is ``ParameterEstimation-Results``.
Now, ``Result`` objects have a lot of different elements, but one is marked as required, so lets start there.
If you've read :doc:`reading-the-schema` this field should be familiar: it's the unique ID that identifies the result.
We'll definitely want to set this, so let's mark down that ``ParameterEstimation-Results-UID`` is one of the paths we will want to modify.

Now, we'll also want to change some other fields in this analysis too. 
Keep in mind that in order to specify *which analysis* we're talking about, we will need the UID path from before - we'll see how exactly to use it shortly.
So, let's say we just want to record what waveform approximant we used, and where to find the result.
Scrolling through the ``ParameterEstimation-Results``, we see ``WaveformApproximant``, which seems like an answer for the first.
For the second, we also see the field ``ResultFile``, which is probably what we want for the second.
Expanding it out though, this field also has sub-fields!
However, this is actually another one our special cases: this is a ``LinkedFile``, 



Flag by Flag
^^^^^^^^^^^^



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