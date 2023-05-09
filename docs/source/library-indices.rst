Understanding Library Indices
=============================

Library indices are summary information about the contents of the library.
Two pieces of information are currently included in this.
First is the datetime of last update, both for individual superevents and the library as a whole.
Second is superevent specific "Labels", a collection of strings which describe the metadata
- see :doc:`library-index-labelling` for more information.
An example is: 

.. code-block::

  {
    "LibraryStatus": {
      "LastUpdated": "2023/04/09 21:11:20"
    },
    "Superevents": [
      {
        "UID": "S230301f",
        "LastUpdated": "2023/04/09 21:11:20",
        "Labels": [
          "PE::high-significance",
          "PE-status::unstarted"
        ]
      },
      {
        "UID": "S230301h",
        "LastUpdated": "2023/04/09 21:11:17",
        "Labels": [
          "PE::high-significance",
          "PE-status::unstarted"
        ]
      },
      {
        "UID": "S230303m",
        "LastUpdated": "2023/04/09 21:11:14",
        "Labels": [
          "PE::high-significance",
          "PE-status::unstarted"
        ]
      },
    ]
  }


It is worth noting that unlike most fields of superevent metadata,
superevent fields in the index allow free addition of properties. 
So, users should feel free to add information to these accordingly.