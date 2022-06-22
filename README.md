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
* For visualization of the json schema, see https://cbc.docs.ligo.org/meta-data/cbc-meta-data-schema.html

### R&D group liaisons

* Richard Udall (PE)
* Wynn Ho (EM)
* Simone Mastrogiovanni (Cosmology)
* Suvodip Mukherjee (cosmology)
* Bruce Edelman (R&P)
* Dimitri Estevez (All-sky)
* Aditya Vijaykumar (TGR)

## cbcflow

This repository contains the source code for `cbcflow` a tool to interact with the metadata. You can find [documentation for this module here](https://cbc.docs.ligo.org/meta-data/index.html)



