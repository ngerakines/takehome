"""Console script for takehome."""
import argparse
import os
import sys
from typing import Dict

from takehome import Indexer, Index


def main():
    """Console script for takehome."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparsers")

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--index", type=str, default="./index", dest="index_file"
    )

    index_args = subparsers.add_parser(
        "index", parents=[parent_parser], help="Create an index."
    )
    index_args.add_argument(
        "location",
        type=str,
        action="extend",
        nargs="+",
    )

    search_args = subparsers.add_parser(
        "search", parents=[parent_parser], help="Search using an index."
    )
    search_args.add_argument("query", type=str, nargs=argparse.REMAINDER)

    args: Dict[str, any] = {}
    args.update(vars(parser.parse_args()))

    if "subparsers" not in args or args["subparsers"] is None:
        parser.print_help()
        return 1

    if args["subparsers"] == "search":
        index = Index()
        index.load_file(args["index_file"])

        query = args["query"]
        if not isinstance(query, list):
            raise Exception("invalid query")
        if len(query) < 1:
            raise Exception("invalid query")

        results = index.search(query[0])
        for result in results:
            print(result)

        return 0

    elif args["subparsers"] == "index":
        locations = args.get("location", [])
        if len(locations) < 1:
            raise Exception("at least one location is required")

        index = Index()
        indexer = Indexer(index=index)
        for location in locations:
            indexer.scan_directory(os.path.abspath(location), scan=True)
        index.to_file(args["index_file"])

        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
