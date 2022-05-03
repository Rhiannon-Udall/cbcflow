import glob
import json
import logging
import os

from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

from .metadata import MetaData

logger = logging.getLogger(__name__)


class GraceDbDatabase(object):
    def __init__(self, service_url):
        self.service_url = service_url

    def pull(self, sname):
        fname = MetaData.get_filename(sname)
        try:
            with GraceDb(service_url=self.service_url) as gdb:
                return json.loads(gdb.files(sname, fname).data)
        except HTTPError:
            logger.info(
                f"No metadata stored on GraceDb ({self.service_url}) for {sname}"
            )
            return {}

    def push(self, metadata):
        logger.info(
            f"Pushing changes for {metadata.sname} to Gracedb ({self.service_url})"
        )
        message = "Updating cbc-meta"
        with GraceDb(service_url=self.service_url) as gdb:
            gdb.writeLog(
                object_id=metadata.sname,
                message=message,
                filename=metadata.library_file,
            )


class LocalLibraryDatabase(object):
    def __init__(self, library, schema, default_data=None):
        """A class to handle operations on the local library (git) database

        Parameters
        ----------
        library: str
            A path to the directory containing the metadata files
        """

        self.library = library
        self.metadata_dict = {}

        if default_data is None:
            default_data = {}

        metadata_list = [
            MetaData.from_file(f, schema, default_data) for f in self.filelist
        ]
        for md in metadata_list:
            self.metadata_dict[md.sname] = md

    @property
    def filelist(self):
        return glob.glob(os.path.join(self.library, "*cbc-metadata.json"))
