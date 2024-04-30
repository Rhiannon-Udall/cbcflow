import argparse

from ..core.schema import get_schema
from ..core.database import LocalLibraryDatabase


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("library", help="The library to convert", type=str)
    args = parser.parse_args()

    v2_schema = get_schema(version="v2")
    v3_schema = get_schema(version="v3")

    library = LocalLibraryDatabase(library_path=args.library, schema=v2_schema)

    library.load_library_metadata_dict()
    library.metadata_schema = v3_schema

    for superevent, metadata in library.metadata_dict.items():
        print(f"Attempting update of {superevent}")
        defaults_update = {
            "Info": {"SchemaVersion": "v3"},
            "CatalogTracking": {
                "ParameterEstimationStatuses": [],
                "SearchResultStatuses": [],
                "Notes": [],
            },
            "GraceDB": {"Events": []},
        }
        for gevent in metadata["GraceDB"]["Events"]:
            defaults_update["GraceDB"]["Events"].append(
                {"UID": gevent["UID"], "Notes": []}
            )
        del metadata.data["Lensing"]["Analyses"]
        metadata.update(defaults_update)
        metadata.write_to_library()
        metadata.validate()
        print("Successfully wrote new defaults to library")
