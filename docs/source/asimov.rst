Asimov Integration
==================

CBCFlow is designed to seamlessly integrate with running `asimov <https://asimov.docs.ligo.org/asimov/>` projects.

By default an asimov project will not write data to a CBCFlow library, but it's easy to inform asimov of the existence of a library using a YAML-format blueprint.

The configuration blueprint in the block below uses a CBCFlow library which has been cloned as ``cbcflow-library`` into the root of the asimov project.
It is set up to write data to the ``ParameterEstimation`` division of the event data.

.. code-block:: yaml

		kind: configuration
		hooks:
		   postmonitor:
		     cbcflow:
		       library location: cbcflow-library
		       schema section: ParameterEstimation
		   applicator:
		     cbcflow:
		       library location: cbcflow-library

This configuration blueprint can be applied by saving the YAML data as ``cbcflow.yaml``, and then running

.. code-block:: console

		$ asimov apply -f cbcflow.yaml

In the root of the asimov project.

The asimov integration uses two separate "hooks" within asimov to function.
The first is the ``postmonitor`` hook.
Here asimov sends the contents of its project ledger to the CBCFlow integration, and CBCFlow digests information about the settings and current status of analyses which are being run.
This is executed automatically each time

.. code-block:: console

		$ asimov monitor

is run manually, or each time the ``asimov start`` cron process performs a monitoring loop over the project's analyses.

The second entrypoint to asimov is via the ``applicator`` hook.
This allows asimov to read data from CBCFlow and use it to create new events in a project.

This can be run using the ``asimov apply`` command, for example, for an event in the library called ``S200000xx``:

.. code-block:: console

		$ asimov apply -p cbcflow -e S200000xx

will add the event and the relevant metadata to the asimov ledger.

The script below will set up an entire project using the ``S200000xx`` event, including cloning the CBCFlow library.
You'll need to replace ``S200000xx`` with a real event name however.
It will then build and start the workflow to analyse the event.

.. code-block:: bash

		asimov init "Test Project"

		asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/testing-pe.yaml
		asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml

		asimov apply -f cbcflow.yaml

		# Clone the git repository
		# NB you will need an access token to use this method
		# and should replace the library URL with your own library
		
		git clone https://oauth2:$ACCESS_TOKEN@git.ligo.org/asimov/test-cbc-workflow.git cbcflow-library
		cd cbcflow-library
		git checkout asimov-integration
		cd ../

		asimov apply -p cbcflow -e S200000xx
		asimov apply -f https://git.ligo.org/asimov/data/-/raw/cbcflow/analyses/get-data.yaml -e S200000xx

		asimov manage build submit
		asimov start
