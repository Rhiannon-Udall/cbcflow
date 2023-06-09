Command Line Interface - Basics
===============================

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

And finally, if you want to practice with the real library instead, you can follow instructions and
links in :doc:`local-library-copy-setup`.

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
