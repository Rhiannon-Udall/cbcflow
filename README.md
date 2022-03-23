# meta-data

A repository to build the JSON schema for CBC meta data in O4 see https://dcc.ligo.org/LIGO-T2100502 for background.

* To add the schema, please clone the repository add lines to `cbc-meta-data.schema` and create a MR.
* The CI will check the validity of the schema, you can do this locally by running
```console
$ pip install jsonschema
$ jsonschema jsonschema -i cbc-meta-data-example.json cbc-meta-data.schema
```
* For help with the json schema, see https://json-schema.org/learn/getting-started-step-by-step.html
