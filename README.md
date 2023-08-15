# CBC Workflow

This is the repository for the CBC Workflow project ("`cbcflow`").
This consists of two parts - a metadata schema which governs the structure of the json files in which data is stored,
and a code base which provides tools to interact with those files. 

## [Documentation](https://cbc.docs.ligo.org/projects/cbcflow/index.html)

This should be the first point of reference for usage and API of cbcflow.
If you would like something to be added to the documentation, please contact the developers.

## The meta-data schema

CBC meta-data for O4 will be stored in structured json files, as recommended by an investigatory committee [here](https://dcc.ligo.org/LIGO-T2100502).
The second version (v2) is currently in use, and is planned for use for the duration of the first part of the fourth observing run (O4a).
For more information on the schema, please see [the appropriate section of the documentation](https://cbc.docs.ligo.org/projects/cbcflow/schema-visualization.html). 

## CBCFlow

`cbcflow` is a set of tools provided for users to interact with the metadata libraries being used. This includes:
- Tools for creating new default metadata files, validating them against the schema and viewing their contents.
- Monitors which pull information on events from GraceDB, according to structured queries.
- An infrastructure for parsing libraries of these events, and configuration of those libraries which structures the aforemenetioned queries.
- Index files which can provide summary information about the contents of libraries.
- Hooks for interacting with Asimov.

### Mattermost Channel

Development of `cbcflow` is principally coordinated through a dedicated mattermost channel, which is open to all collaboration members, found [here](https://chat.ligo.org/ligo/channels/cbcflow-development).

For help with the usage of `cbcflow`, there is also a dedicated help channel, open to all collaboration members, which may be found [here](https://chat.ligo.org/ligo/channels/cbcflow-help).

### Development Calls

Development calls take place every other Wednesday at 8 PST / 11 EST / 16 UTC, and will take place on the CBC channel of teamspeak. Any interested collaboration member is welcome to attend. 

### Developers
* Gregory Ashton
* Rhiannon Udall
* Zach Yarbrough

### R&D Group Liaisons

* Rhiannon Udall (PE)
* Wynn Ho (EM)
* Simone Mastrogiovanni (Cosmology)
* Suvodip Mukherjee (cosmology)
* Aditya Vijaykumar (TGR)
* Ronaldas Macas (Detchar)
* Siddharth Soni (Detchar)
* Apratim Ganguly (Lensing)
* Ka-Lok Lo (Lensing)
* Ethan Payne (R&P)
* Shio Sakon (All-sky)

## Past R&D Group Liaisons

* Dimitri Estevez (All-sky)
* Bruce Edelman (R&P)


