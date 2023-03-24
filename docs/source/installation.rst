============
Installation
============

Installing cbcflow from release
----------------------------------

.. tabs::

   .. tab:: pypi

      NOT YET IMPLEMENTED
      To install the latest :code:`cbcflow` release from `PyPi
      <https://pypi.org/project/cbcflow/>`_, run

      .. code-block:: console

         $ pip install --upgrade cbcflow

Install cbcflow for development
----------------------------------

To install ``cbcflow`` for development, run

.. code-block:: console

   $ git clone git@git.ligo.org:cbc/meta-data.git
   $ cd meta-data/
   $ pip install -e .

For development, we will use ``pre-commit`` to check standardisation.
For help with this, see `the documentation <https://pre-commit.com/>`__.
In short, run

.. code-block::

   $ pip install pre-commit
   $ pre-commit install

Then, when you create a git commit, ``pre-commit`` will try to
standardize your changes. If there are changes, you will then need to
add them and commit again. In some cases, ``pre-commit`` will print out
suggested changes that are required (e.g. when there are spelling
errors), but not fix them automatically. Here, you will need to fix the
software directly, add, and then commit.

Note that if you do not install ``pre-commit``, you can still push, but
if the standardisation checks fail, the C.I. on gitlab will fail.

If you experience issues, you can commit with ``--no-verify`` and push
then request help (cc @gregory.ashton).

