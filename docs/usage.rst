CBCFlow Usage
=============

Getting help
------------

Run

.. code:: console

   $ cbcflow --help

for help in how to use the program.

Argcomplete
-----------
``cbcflow`` uses `argcomplete <https://pypi.org/project/argcomplete/>`__
to help with setting arguments. There is a global completion setup (see
the documentation), but a fallback (often useful on clusters with
changing environments) is to register the executable directly. This can
be done by running

.. code-block::

   $ eval "$(register-python-argcomplete cbcflow)"

Note, this command requires that you have installed ``argcomplete``.

Once initialised, you can tab complete to get help with setting elements
of the metadata. For example,

.. code-block::

   $ cbcflow SXXYYZZabc --info-[TAB]

will either auto complete all the ``--info-`` options, or print a list
of available options.


Developmen
