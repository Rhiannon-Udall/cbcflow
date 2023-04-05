#!/usr/bin/env python

import glob
import os
import shutil

import setuptools

files = glob.glob("schema/*schema")
tdir = "src/cbcflow/schema/"
if os.path.exists(tdir) is False:
    os.mkdir(tdir)
for file in files:
    dst = os.path.join(tdir, os.path.basename(file))
    shutil.copy(file, dst)

if __name__ == "__main__":
    setuptools.setup(
        package_data={
            "cbcflow": [
                "schema/cbc-meta-data-v1.schema",
                "schema/cbc-meta-data-v2.schema",
                "schema/index-v1.schema",
            ]
        },
    )
