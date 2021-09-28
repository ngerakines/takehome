# Take Home Project

Challenge: A directory contains multiple files and directories of non-uniform file and directory names. Create a program that traverses a base directory and creates an index file that can be used to quickly lookup files by name, size, and content type.

# Usage

First, create the index using the `index` subcommand.:

    $ takehome index

Once the index is created, the search subcommand can be used to query it.

    $ takehome search "or file_name=sample.pdf (and file_name=user1.json file_size=16)"
