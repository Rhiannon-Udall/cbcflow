Index Labelling
===============

Understanding Labelling
-----------------------

The CBCFlow labeller exists principally for usage with the gitlab CI, but can be extended in the future.
The central concept is that we want a way to flexibly apply labels to index entries based on the metadata of superevents.
Prototypically, one may then use those labels to label gitlab issues, for easy tracking and visibility. 
We have defined the parent class ``cbcflow.database.Labeller``,
which in conjunction with the ``cbcflow.database.LocalLibraryDatabase`` object does most of the programmatic heavy lifting.

Once desired functionality has been put into an appropriate child class (see below), usage should be as simple as passing
the new Labeller subclass to the method ``label_index_file`` method of a ``LocalLibraryDatabase`` instance.
That instance will then have an index where for each ``Superevent`` element there is a field ``Labels`` which contains all 
of the labels assigned according to the desired algorithm. 

Writing Your Own ``Labeller`` Child Class
-----------------------------------------

We will go over how one would construct a Labeller called ``MyLabeller`` as an example.
The standard incantation to subclass in the desired way is:

.. code-block::

    from cbcflow.database import Labeller

    class MyLabeller(Labeller):
        """An example of writing our own labeller"""

        def __init__(self, library: "LocalLibraryDatabase") -> None:
            """Setup the labeller

            Parameters
            ==========
            library : `LocalLibraryDatabase`
                A library object to access for index and metadata
            """
            super(MyLabeller, self).__init__(library)

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


Using the Labeller
------------------

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

Gitlab CI Usage
---------------

Much of the integration with the gitlab CI depends more on the gitlab python API than cbcflow per se,
and so it's encouraged to use that documentation for further information.
We present our example (as of time of writing) of how to implement a python script which may be called in the CI to apply labels and read those labels into corresponding issues for each event.

.. code-block::

    import cbcflow
    import gitlab
    import os
    import re
    import logging
    import json

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    # Modification on original script at
    # https://git.ligo.org/cbc/projects/cbc-workflow-test-library-a/-/blob/main/update_issue_tracker.py

    # Read in the local library and metadata_dict
    library = cbcflow.database.LocalLibraryDatabase(
        library_path=".",
    )

    class DevelopmentLibraryLabeller(cbcflow.database.Labeller):
        """This is a labeller being used for test development, defined within the library to allow rapid development"""

        def __init__(self, library: "cbcflow.database.LocalLibraryDatabase") -> None:
            """Setup the labeller

            Parameters
            ==========
            library : `LocalLibraryDatabase`
                A library object to access for index and metadata
            """
            super(DevelopmentLibraryLabeller, self).__init__(library)

        def label_event(self, event_metadata: "cbcflow.metadata.MetaData") -> list:
            """Generate the labels we want for this event

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

    # Generate an index for our library
    # This is technically unneceessary since it's done by label_index_file
    # But included here for demonstration purposes
    library.generate_index_from_metadata()

    # Get the labelling using the Labeller we wrote
    library.label_index_file(DevelopmentLibraryLabeller)

    # A convenience object
    labelled_index_superevents = {x["Sname"]:x for x in library.working_index["Superevents"]}

    # Set up the gitlab project
    gl = gitlab.Gitlab(os.environ['CI_SERVER_URL'], private_token=os.environ['PRIVATE_TOKEN'])
    project = gl.projects.get(os.environ['CI_PROJECT_ID'])


    # Get a list of existing issues
    issues = project.issues.list(get_all=True, state="opened")
    issue_dict = {issue.title: issue for issue in issues}

    logger.info(issue_dict.keys())

    # Check all events have issues
    for sname in labelled_index_superevents.keys():
        if sname not in issue_dict.keys():
            issue_details = {
                'title': sname,
                'description': f'Discussion of {sname}',
            }
            issue = project.issues.create(issue_details)


    # Pull latest set of issues
    issue_dict = {issue.title: issue for issue in issues}

    # Extract git repo
    library._initialize_library_git_repo()
    repo = library.repo

    # Extract last message
    message = library.repo.head.commit.message

    # Extract changes
    for element in message.split(" "):
        if re.match("^S[0-9]{6}[a-z]+", element):
            sname = element
            issue_dict[sname].discussions.create({'body': message})

    # Set the labels for all issues
    for sname, issue in issue_dict.items():
        if sname in labelled_index_superevents.keys():
            issue = issue_dict[sname]
            superevent_data = labelled_index_superevents[sname]

            for label_string in superevent_data["Labels"]:
                label = project.labels.get(label_string)
                issue.labels.append(label.name)

            issue.save()
