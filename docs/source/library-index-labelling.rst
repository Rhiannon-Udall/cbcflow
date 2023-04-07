# Index Labelling

## Understanding Labelling

The CBCFlow labeller exists principally for usage with the gitlab CI, but can be extended in the future.
The central concept is that we want a way to flexibly apply labels to index entries based on the metadata of superevents.
Prototypically, one may then use those labels to label gitlab issues, for easy tracking and visibility. 
We have defined the parent class ``cbcflow.database.Labeller``,
which in conjunction with the ``cbcflow.database.LocalLibraryDatabase`` object does most of the programmatic heavy lifting.

Once desired functionality has been put into an appropriate child class (see below), usage should be as simple as passing
the new Labeller subclass to the method ``label_index_file`` method of a ``LocalLibraryDatabase`` instance.
That instance will then have an index where for each ``Superevent`` element there is a field ``Labels`` which contains all 
of the labels assigned according to the desired algorithm. 

## Writing Your Own ``Labeller`` Child Class

We will go over how one would construct the ``StandardLabeller`` as an example.
The standard incantation to subclass in the desired way is:

.. code-block::

    from cbcflow.database import Labeller

    class MyLabeller(Labeller):
        """The default labeller. NOTE this is presently considered an example of barebones usage only!
        For ongoing development, please write an analogous Labeller, within the library's git CI."""

        def __init__(self, library: "LocalLibraryDatabase") -> None:
            """Setup the labeller

            Parameters
            ==========
            library : `LocalLibraryDatabase`
                A library object to access for index and metadata
            """
            super(StandardLabeller, self).__init__(library)

Now, most of the functionality is taken care of by subclassing ``Labeller``.
The only thing we need to define is ``label_event`` which will take in superevent metadata and put out a list of labels.
Considering ``MyLabeller`` again, we have:

.. code-block::

    def label_event(self, event_metadata: "MetaData") -> list:
        """Generate standard CBC library labels for this event

        Parameters
        ==========
        event_metadata : `cbcflow.metadata.MetaData`
            The metadata for a given event, to generate labels with

        Returns
        =======
        list
            The list of labels from the event metadata
        """
        # Get preferred event
        preferred_event = None
        for event in event_metadata.data["GraceDB"]["Events"]:
            if event["State"] == "preferred":
                preferred_event = event

        labels = []
        if preferred_event:
            # Add PE significance labels
            pe_high_significance_threshold = 1e-30
            pe_medium_significance_threshold = 1e-10
            if preferred_event["FAR"] < pe_high_significance_threshold:
                labels.append("PE::high-significance")

            elif preferred_event["FAR"] < pe_medium_significance_threshold:
                labels.append("PE::medium-significance")
            else:
                labels.append("PE::below-threshold")

            # Add PE status labels
            status = event_metadata.data["ParameterEstimation"]["Status"]
            labels.append(f"PE-status::{status}")

        return labels

We can go through the functionality here, with :doc:`schema-visualization` as our guide.
First, we are taking in ``MetaData`` and putting out a list, as expected.
We figure out the preferred event within the superevent by looking through all the events and choosing the one whose state is "preferred".
Then, we set our thresholds, and check which threshold the preferred event's ``FAR`` value clears.
Next, we check the status of the ParameterEstimation, and write that directly as a label type.
We add these labels to our labels list, and return it - that's it!
One thing worth noting is the peculiar format of these labels: chosen to fit with the labelling system within gitlab.
For more details on how that works, see below, though note that there is more flexibility, since that is not directly part of ``cbcflow``.


## Using the Labeller

To use the labeller, assuming we have a library with populated metadata, we do (assuming we have already defined a ``Labeller`` as described above):

.. code-block::

    # Get the LocalLibraryDatabase class
    from cbcflow.database import LocalLibraryDatabase

    # Initialize it from a path as normal
    testlibrary = LocalLibraryDatabase("/path/to/my/library")

    # This is the workhorse command
    # This will automatically generate a working_index from the metadata stored in the library
    # (You can also generate that working index yourself with the generate_index_from_metadata method)
    # By passing MyLabeller as we've written it, cbcflow will take care of looping through the events and applying the labels
    testlibrary.label_index_file(MyLabeller)
    # Now that we're finished, we write it to a file in the library
    testlibrary.write_index_file()

That's all! 
For practical purposes, you will also want to write code for handling the gitlab CI, which is more involved, but from the CBCFlow side this is it.
All user development is about the logic in ``label_event``, which can be made to reflect whatever purposes you have. 

## Gitlab CI Usage

