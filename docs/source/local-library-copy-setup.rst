Setting Up A Library From a Remote
==================================

Before interacting with a library, one naturally needs a library to interact with.
If you only wish to read metadata, and are on the CIT shared filesystem, this is easy:
you may read from the shared CBC account library at `CIT:/home/cbc/cbcflow/O4a/cbc-workflow-o4a`.

If you wish to modify metadata, however, you will need to interact with a local copy.
You may choose to fork the central repository and clone that, or you may clone it directly.
Note that the main branch of this library will be protected, and so you will need to make
updates by branching and making a merge request - as we will see this is done automatically 
when using provided scripts. 

Cloning and Setup
-----------------

Creating a working ``cbcflow`` library is *slightly* more complicated than just cloning a remote library.
First, though, you should indeed clone it!
For O4a the relevant library to clone is https://git.ligo.org/cbc/projects/cbc-workflow-o4a/.
So, using an ssh key to access gitlab, this looks like: 

.. code-block::

    (igwn) [rhiannon.udall@ldas-pcdev5 tutorials]$ git clone git@git.ligo.org:cbc/projects/cbc-workflow-o4a

Once that's done, there's one more thing to do!
Run the script ``setup-cbcflow-merge-strategy.sh`` - so, e.g. 

.. code-block::

    (igwn) [rhiannon.udall@ldas-pcdev5 tutorials]$ cd cbc-workflow-o4a/
    (igwn) [rhiannon.udall@ldas-pcdev5 cbc-workflow-o4a]$ ./setup-cbcflow-merge-strategy.sh

And that's it!
If you would like to know *why* you did that other step, see below.

Custom Git Merging in CBCFlow
-----------------------------

``cbcflow`` requires custom a custom driver for ``git merge`` to handle json files (see :doc:`cbcflow-git-merging` for details).
This can be offloaded entirely, as long as we configure our library correctly, but this must be done locally since the relevant configuration cannot be globally tracked.
This also means that valid merging can *only* be done locally - you can't just hit merge in gitlab and expect it all to work!
In real usage this should be handled by a team of experts (reach out if you want to join that team!), but for local usage we do want to make sure things get setup right.
The library you have cloned, assuming it is setup correctly according to :doc:`library-setup-from-scratch`, will have the files ``.gitattributes``, ``.gitconfig``, and ``setup-cbcflow-merge-strategy.sh``.
If those files aren't present, it's very easy to make them yourself, just follow the instructions on :doc:`library-setup-from-scratch`.