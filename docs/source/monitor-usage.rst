Using the GraceDB Monitor
=========================

To use the monitor, one should first configure ``cbcflow`` and a library upon which the monitor will act. 
If you have not already done so, please see :doc:`configuration` and :doc:`library-setup` respectively for further details.

To run the monitor, we execute the command ``cbcflow_monitor_make``, which sets up the ``monitor.sub`` file and submits it to htcondor. The flags we will use are:

.. code-block::
    
    cbcflow_monitor_make --config-file review-monitor.cfg --ligo-user-name rhiannon.udall \
    --ligo-accounting ligo.dev.o4.cbc.explore.test --rundir `pwd` --monitor-interval 1 --monitor-minute {}

The ``config-file`` points to the configuration file being used, in case it differs from the default configuration,
and ``--ligo-user-name`` and ``ligo-accounting`` have their standard meaning.
``--monitor-interval`` sets that hour interval at which the monitor will run - 1 means every hour while the default is 2, or every other hour.
Finally ``--rundir`` sets the directory in which the monitor ``.sub`` and output files will reside. 

The one free field here is the ``monitor-minute``:
if left empty the monitor will run on the hour, while if a value (an integer from 0 to 59) is passed the monitor will run at that minute on the hour.
This primarily exists as a convenience when testing, as otherwise one may need to wait up to an hour to see the results of a test.
If you wish to use this, it is recommended to add 6 to your present minute on the hour, as this will give the optimal chance of running correctly at that time.

Once you have run this, your set!
The monitor will run at the requested interval through htcondor, 
and you can check it's output in the ``monitor.err`` file in the run directory.
