import json

from ligo.gracedb.exceptions import HTTPError
from ligo.gracedb.rest import GraceDb

from .metadata import MetaData


class Database(object):
    def __init__():
        pass

    def fetch(sname):
        """Fetch existing information for the event from the database

        Parameters
        ----------
        sname: str
            The superevent name

        Returns
        -------
        metadata_dict: dict
            A dictionary of the metadata stored in the database
        """
        pass


class GraceDbDatabase(Database):
    def __init__(self, service_url="https://gracedb-test.ligo.org/api/"):
        self.service_url = service_url

    def pull(self, sname):
        fname = MetaData.get_filename(sname)
        try:
            with GraceDb(service_url=self.service_url) as gdb:
                return json.loads(gdb.files(sname, fname).data)
        except HTTPError:
            print(f"No metadata stored on GraceDb ({self.service_url}) for {sname}")
            return {}

    def push(self, metadata):
        print(f"Pushing changes for {metadata.sname} to Gracedb ({self.service_url})")
        message = "Updating cbc-meta"
        with GraceDb(service_url=self.service_url) as gdb:
            gdb.writeLog(
                object_id=metadata.sname,
                message=message,
                filename=metadata.library_file,
            )
