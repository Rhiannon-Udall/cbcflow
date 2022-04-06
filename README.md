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

### R&D group liaisons

* Richard Udall (PE)
* Wynn Ho (EM)

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

### Development
To install `cbcflow` for development, run
```
$ pip install -e .
```
For development, we will use `pre-commit` to check standardisation. For help
with this, see [the documentation](https://pre-commit.com/). In short, run
```
$ pip install pre-commit
$ pre-commit install
```
Then, when you create a git commit, `pre-commit` will try to standardize your
changes. If there are changes, you will then need to add them and commit again.
In some cases, `pre-commit` will print out suggested changes that are required
(e.g. when there are spelling errors), but not fix them automatically. Here, you
will need to fix the software directly, add, and then commit.

Note that if you do not install `pre-commit`, you can still push, but if the
standardisation checks fail, the C.I. on gitlab will fail.

If you experience issues, you can commit with `--no-verify` and push then request
help (cc @gregory.ashton).

