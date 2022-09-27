# Example of using cbcflow

## Set up a git library
`cbcflow` stores a local copy of the metadata files for events in a library (a
directory containing all the `.json` files that have been pulled/created). By
default, this is assumed to be a git repository and changes are committed
automatically (this feature can be disabled).

As an example, lets pull a remote repository that has been initialised:
```
LIBRARY_URL=git@git.ligo.org:gregory.ashton/cbcflow-library-example.git
LIBRARY=cbcflow-library-example/
$ git clone $LIBRARY_URL
$ cd $LIBRARY && git pull && cd ..
```

If you create a new repository, you will need to add a single commit (e.g.,
add a README).

## Configuration
Options can be set on the command line, but this often leads to long and
difficult to parse inputs. To remove some boilerplate, we can write a config
file `~/.cbcflow.cfg` with the GraceDb service URL and path to the git library
```
$ echo "[cbcflow]" > ~/.cbcflow.cfg
$ echo "gracedb_service_url=https://gracedb-test.ligo.org/api/" >> ~/.cbcflow.cfg
$ echo "library = /home/gregory.ashton/testing/cbcflow-library-example/" >> ~/.cbcflow.cfg
```

## Pull an event and add a label

Okay, so now let's pull down any existing metadata from GraceDb for the event
`S220401a`. Then, we'll update the labels and push our changes back to GraceDb
for others to use
```
$ EVENT=S220401a
$ cbcflow $EVENT --pull-from-gracedb
INFO:cbcflow.schema:Using schema file /nfshome/store03/users/gregory.ashton/public_html/projects/meta-data/src/cbcflow/schema/cbc-meta-data-v1.schema
INFO:cbcflow.metadata:No library file: creating defaults
INFO:cbcflow.database:No metadata stored on GraceDb (https://gracedb-test.ligo.org/api/) for S220401a
INFO:cbcflow.metadata:Writing file /home/gregory.ashton/testing/cbcflow-library-example/S220401a-cbc-metadata.json

$ cbcflow $EVENT --update --info-labels-add SOME_LABEL
INFO:cbcflow.schema:Using schema file /nfshome/store03/users/gregory.ashton/public_html/projects/meta-data/src/cbcflow/schema/cbc-meta-data-v1.schema
INFO:cbcflow.metadata:Found existing library file: loading
INFO:cbcflow.metadata:Changes between loaded and current data:
INFO:cbcflow.metadata:{'info': {'labels': ['SOME_LABEL']}}
INFO:cbcflow.metadata:Writing file /home/gregory.ashton/testing/cbcflow-library-example/S220401a-cbc-metadata.json

$ cbcflow $EVENT --push-to-gracedb
INFO:cbcflow.schema:Using schema file /nfshome/store03/users/gregory.ashton/public_html/projects/meta-data/src/cbcflow/schema/cbc-meta-data-v1.schema
INFO:cbcflow.metadata:Found existing library file: loading
INFO:cbcflow.database:Pushing changes for S220401a to Gracedb (https://gracedb-test.ligo.org/api/)
```

In this example, GraceDb does not already contain a metadata file for the
event. Therefore, it writes some defaults (based on the JSON schema) to disk
(these can be seen in the example below).

When we update the metadata, we need to pass both `--update` and the command line
of what we want to update, in this case `--info-labels-add SOME_LABEL`. The
command line is build directly from the schema. So, the command above will add
the label `SOME_LABEL` to `metadata["info"]["labels"]` which is an array. We can
look at the file directly to check this is the case:
```
{
  "sname": "S220331a",
  "info": {
    "labels": [
      "SOME_LABEL"
    ]
  },
  "publications": {
    "papers": []
  },
  "parameter_estimation": {
    "analysts": [],
    "reviewers": [],
    "status": "NOT STARTED",
    "results": []
  }
}
```

Whenever we make changes, there is a print out which we can check. The output is
fairly verbose, during testing this is useful, but as we switch to production
some of these messages will be relegated to debug statements.

### Types of arguments

Above, we used the argument `--info-labels-add` to append a label to the list
of labels in `info`. If you take a look at the help (i.e., run `cbcflow --help`),
you will notice there are three types of arguments used to set elements of the
metadata. These are:

1. `--XX-YY-add`: append the new item to the array
2. `--XX-YY-remove`: remove an existing item from the array
3. `--XX-YY-set`: Set the item. This applies to any element which is not an array

### Fix a typo
Okay, so what would we do if we added the wrong label? We can use the remove
option! For example,
```
EVENT=S220331a
cbcflow $EVENT --pull-from-gracedb
cbcflow $EVENT --update --info-labels-add SOME_LABLE
cbcflow $EVENT --update --info-labels-remove SOME_LABLE
cbcflow $EVENT --update --info-labels-add SOME_LABEL
cbcflow $EVENT --push-to-gracedb
```
Note that, the entire history of this process is stored in the git library. We
can check that by running
```
$ cd $LIBRARY
$ git log S220331a-cbc-metadata.json
commit 5a50575f7d997a93d6cfe71b79e35f439148b063
Author: Gregory Ashton <gregory.ashton@ligo.org>
Date:   Thu Apr 7 15:13:01 2022 +0100

    Changes made to [info]
    cmd line: /home/gregory.ashton/.conda/envs/flow/bin/cbcflow S220331a --update --info-labels-add SOME_LABEL

commit 78c8fe27acb137b234e6a57ed6d61dea430d3d12
Author: Gregory Ashton <gregory.ashton@ligo.org>
Date:   Thu Apr 7 15:13:00 2022 +0100

    Changes made to [info]
    cmd line: /home/gregory.ashton/.conda/envs/flow/bin/cbcflow S220331a --update --info-labels-remove SOME_LABLE

commit 35c5b42cb533ee8f67c75dda534c445fa19c4c1c
Author: Gregory Ashton <gregory.ashton@ligo.org>
Date:   Thu Apr 7 15:13:00 2022 +0100

    Changes made to [info]
    cmd line: /home/gregory.ashton/.conda/envs/flow/bin/cbcflow S220331a --update --info-labels-add SOME_LABLE

commit 9a215a5b7910c1c92f90ca885739b048e8b81891
Author: Gregory Ashton <gregory.ashton@ligo.org>
Date:   Thu Apr 7 15:13:00 2022 +0100

    Changes made to [$replace]
    cmd line: /home/gregory.ashton/.conda/envs/flow/bin/cbcflow S220331a --pull-from-gracedb
```

### A more involved example

Okay, finally let's look at a more interesting example. Here, we pull the
existing metadata, add a label, and then set the PE properties.
```
$ EVENT=S220331b
$ cbcflow $EVENT --pull-from-gracedb
$ cbcflow $EVENT --update --info-labels-add SOME_LABEL
$ cbcflow $EVENT --update --parameter-estimation-analysts-add gregory.ashton
$ cbcflow $EVENT --update --parameter-estimation-status-set UNDERWAY
$ cbcflow $EVENT --update \
    --parameter-estimation-results-UID-set ProdF1 \
    --parameter-estimation-results-config-file-set CIT:/home/gregory.ashton/O4/runs/S220331b/ProdF1.ini
$ cbcflow $EVENT --push-to-gracedb
```

Note that, for the PE results, the UID is required (there can be multiple sets
of results).

### Viewing the files on GraceDb

You can find the files on GraceDb by following "Data" link, see, e.g.
[here](https://gracedb-test.ligo.org/superevents/S220331b/view/). You will
notice there are several
[files](https://gracedb-test.ligo.org/superevents/S220331b/files/), with
trailing comma and number. This is GraceDb's internal method of versioning.
This provides some element of history to the metadata: every push will create
a new file.

### Conflicts
The outline of `cbcflow` above leaves open the possibility for conflicts. This
could arise, for example, if two people both pull an event, change the metadata,
and then push the event. In practice, whoeever pushes last will simply overwrite
the changes made by the previous editor. This is not desirable behaviour and
needs to be fixed ahead of O4.



