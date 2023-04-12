Command Line Interface
==========================

For many users, the main tool for interacting with ``cbcflow`` metadata are the suite of command line tools.
These allow you to:
#. Print the contents of a metadata file
#. Pull GraceDB information into a metadata file
#. Update a metadata file using a series of flags
#. Update a metadata file by writing a file containing many changes
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
Writing out the path for that gives us ``ParameterEstimation-Results-WaveformApproximant``.
For the second, we also see the field ``ResultFile``, which is probably what we want for the second.
Expanding it out though, this field also has sub-fields!
However, this is actually another one our special cases: this is a ``LinkedFile``, which means we should focus on one element in particular, ``Path``.
If we update this with a valid path on the cluster, then the other required fields - ``MD5Sum`` and ``DateLastModified`` - will be filled in automatically.
So, we can add one more schema path to our list ``ParameterEstimation-Results-ResultFile-Path``.

To summarize, making our desired changes will require updating three paths:

#. ``ParameterEstimation-Results-UID``, telling us which analysis we are modifying.
#. ``ParameterEstimation-Results-WaveformApproximant``, noting the waveform approximant we used.
#. ``ParameterEstimation-Results-ResultFile-Path``, populating information about our result.

Note that we could do the second or the third without each other 
- you can update the waveform approximant without updating the results path or vice versa -
but updating either requires specifying a UID, so we know what we are modifying.
Now that we know what we want to update, let's see how to actually do it!


Flag by Flag
^^^^^^^^^^^^

To update a piece of metadata directly from command lines, we will need the command ``cbcflow_update_from_flags``.
This command takes:

#. The superevent we want to modify
#. Optionally the library in which that superevent is located - if none is given it will go to the configuration default.
#. A set of updates to apply.

Let's say we're working with ``S230409it`` in our library, so the start of the command will be ``cbcflow_update_from_flags S230409it``. 
We're assuming that we have the tutorial library configured as default, but if we don't we can add ``--library /path/to/library/`` as well.

Now, how do we write out the updates?
We have the paths to the changes we want to make, but we also need to know the magic key words that tell us *how* to modify something.
Luckily, there are only 3: ``set``, ``add``, and ``remove``.
It's probably pretty intuitive what those mean, but we can dig into them a bit.
The most common key word is ``set``: if any field is not an array (that is to say, is a string or a number), ``set`` is what we want to use.
By contrast, ``add`` and ``remove`` are used when the field is an array, but importantly only the *last* field.
That is to say, in our example above, ``ParameterEstimation-Results`` is an array, but we are modifying fields within it, so we don't want to use ``add`` or ``remove``.
By contrast, for ``ParameterEstimation-Analysts``, our final field is ``Analysts``, which is an array, so here ``add`` and ``remove`` are appropriate!
Intuitively, ``add`` appends an element to the end of the array, while ``remove`` searches the array for the element and removes it if possible.

Alright, so we know what key words we want to use, and we know our paths, how do we put them together?
Easily enough, the flag to make a change is just ``--{path}-{key word}``.
So, we already know we want to ``add`` something to ``ParameterEstimation-Analysts``, and hence this becomes
``--ParameterEstimation-Analysts-add``, followed by the value you want to add (in quotes if there is a space in the string).
Notice that every term in the path is in Pascal case, while the key word at the end is all lower case -
this is done for technical reasons, but it also helps differentiate the path from the key word.
Putting what we have so far together, this command will look like:

.. code-block::

  cbcflow_update_from_flags S230409it --ParameterEstimation-Analysts-add "Name"

where naturally "Name" is your name!

Now, we also want to make some changes to a result.
All of these are modifying a field that's not an array, so all of them will use ``set``.
For our ``UID``, we have ``--ParameterEstimation-Results-UID-set``, and lets call our result "Tutorial1".
Notice that the ending of this flag is ``-UID-set``: this is one of the two magic combinations in ``cbcflow``.
This designates that this flag is setting which analysis we modify, and so must always be included if we want to modify that analysis.
Moreover, if this specific combination appears at the end of a command, you know that is what it *must* mean.

To add our other entries to the analysis, we can follow the formula.
Setting the waveform approximant give ``--ParameterEstimation-Results-WaveformApproximant-set``,
and setting the ``ResultFile`` path gives ``--ParameterEstimation-Results-ResultFile-Path-set``. 
This second case, ``-Path-set``, is the other magic combination in ``cbcflow``: it means that we are setting a ``LinkedFile`` path,
and so as long as we give a valid path on the cluster some extra machinery will trigger to fill out supporting information.
Now, notice that in each of these *nothing specifies the analysis we are editing* - that must be done by passing the ``UID`` along with them,
regardless of whether the analysis object is being newly created or updated.

So for example, we could pass all of these together as:

.. code-block::

  cbcflow_update_from_flags S230409it --ParameterEstimation-Results-UID-set Tutorial1 \
  --ParameterEstimation-Results-WaveformApproximant-set MyAwesomeWaveform \
  --ParameterEstimation-Results-ResultFile-Path-set /path/to/a/file

or we could make the object first and add one attribute:

.. code-block::

  cbcflow_update_from_flags S230409it --ParameterEstimation-Results-UID-set Tutorial1 \
  --ParameterEstimation-Results-WaveformApproximant-set MyAwesomeWaveform 

then update it with another attribute:

.. code-block::

  cbcflow_update_from_flags S230409it --ParameterEstimation-Results-UID-set Tutorial1 \
  --ParameterEstimation-Results-ResultFile-Path-set /path/to/a/file

But no matter what we always *have* to specify the UID.
This also means that we can't modify more than one analysis with the same call:
if we want to also add an analysis "Tutorial2", it will need to be done in a separate call to the command.

From a File
^^^^^^^^^^^

TODO