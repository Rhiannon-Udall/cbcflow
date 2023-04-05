Understanding Library Indices
=============================

Library indices are summary information about the contents of the library.
Currently, this is very sparse, consisting only of events which satisfy the library configuration and their datetime of last update,
along with the datetime at which the library as a whole was last updated.
An example is: 

.. code-block::

  {
    "LibraryStatus": {
      "LastUpdated": "2023-04-04 15:48:14"
    },
    "Superevents": [
      {
        "Sname": "S230401bm",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230401br",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230401cc",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230401ea",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230401h",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230401j",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230402as",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230402cr",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230402dv",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230402fd",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230402fo",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230403t",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230404aq",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230404ce",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230404df",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230404ia",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230404jc",
        "LastUpdated": "2023-04-04 15:48:14"
      },
      {
        "Sname": "S230404ko",
        "LastUpdated": "2023-04-04 15:48:14"
      }
    ]
  }

However, it is worth noting that unlike most fields of superevent metadata,
superevent fields in the index allow free addition of properties. 
That is, if it is desired to downselect events of interest then tag them with identifying information,
indices provide a useful infrastructure for doing so.