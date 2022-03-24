# CBC Workflow

## The meta-data schema

This repository hosts the JSON schema for CBC meta data in O4 see https://dcc.ligo.org/LIGO-T2100502 for background.

* To add to the schema, please clone the repository add lines to `schema/cbc-meta-data-v1.schema` and create a MR.
* The CI will check the validity of the schema, you can do this locally by running
```console
$ pip install jsonschema
$ jsonschema jsonschema -i tests/cbc-meta-data-example.json schema/cbc-meta-data-v1.schema
```
* For help with the json schema, see https://json-schema.org/learn/getting-started-step-by-step.html

## cbcflow

This repository contains the source code for `cbcflow` a tool to interact with the metadata.

### Installation

To install `cbcflow` for development, clone this repository and run:
```console
$ pip install -e .
```

### Getting help
Run
```console
cbcflow --help
```
for help in how to use the program.
