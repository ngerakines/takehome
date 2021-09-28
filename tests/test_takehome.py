#!/usr/bin/env python

import os

from takehome.takehome import (
    Index,
    Indexer,
    AndMatcher,
    IndexedFile,
    OrMatcher,
    FileNameMatcher,
    parse_nested_tokens,
    scrub_stack,
)

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")

EXPECTED_LOCATIONS = sorted(
    os.path.join(FIXTURE_DIR, loc)
    for loc in [
        "sample.pdf",
        "random-forest.png",
        "linear-regression-plot.jpg",
        os.path.join("data", "user1.json"),
        os.path.join("data", "user2.json"),
    ]
)


def test_index():
    assert str(FIXTURE_DIR).endswith(os.path.join("takehome", "tests", "test_data"))
    index = Index()
    indexer = Indexer(index)
    assert index is not None
    assert indexer is not None

    indexer.scan_directory(FIXTURE_DIR)

    assert sorted(index.files.keys()) == EXPECTED_LOCATIONS

    # Scanning does not produce duplicate records.
    indexer.scan_directory(FIXTURE_DIR)
    assert sorted(index.files.keys()) == EXPECTED_LOCATIONS

    assert os.path.join(FIXTURE_DIR, "sample.pdf") in index.to_string()


def test_query():
    sample_pdf = IndexedFile(os.path.join(FIXTURE_DIR, "sample.pdf"))
    sample_pdf.scan()

    assert AndMatcher([]).match(sample_pdf) is False
    assert OrMatcher([]).match(sample_pdf) is False

    assert FileNameMatcher("sample.pdf").match(sample_pdf) is True
    assert FileNameMatcher("user1.json").match(sample_pdf) is False
    assert (
        AndMatcher(
            elements=[FileNameMatcher("sample.pdf"), FileNameMatcher("user1.json")]
        ).match(sample_pdf)
        is False
    )
    assert (
        OrMatcher(
            elements=[FileNameMatcher("sample.pdf"), FileNameMatcher("user1.json")]
        ).match(sample_pdf)
        is True
    )


def test_parse_tokens():
    assert parse_nested_tokens("") == ([], [], 0, "")
    assert parse_nested_tokens("hello world") == (["hello", "world"], [], 0, "")
    assert parse_nested_tokens('"hello world"') == (["hello world"], [], 0, "")
    assert parse_nested_tokens('name=Nick age=37 location="Dayton, OH"') == (
        ["name=Nick", "age=37", "location=Dayton, OH"],
        [],
        0,
        "",
    )
    assert parse_nested_tokens("and name=nick (or age=37 age=38)") == (
        ["and", "name=nick"],
        [(["or", "age=37", "age=38"], [], 17, "")],
        0,
        "",
    )
    assert parse_nested_tokens("and (or (a=a) b=b) (or c=c d=d)") == (
        ["and", ""],
        [
            (
                ["or", "", "b=b"],
                [(["a=a"], [], 4, " b=b) (or c=c d=d)")],
                13,
                " (or c=c d=d)",
            ),
            (["or", "c=c", "d=d"], [], 11, ""),
        ],
        0,
        "",
    )


def test_scrub_stack():
    assert scrub_stack(parse_nested_tokens("and (or (a=a) b=b) (or c=c d=d)")) == (
        ["and"],
        [
            (
                ["or", "b=b"],
                [(["a=a"], [], 0, "")],
                0,
                "",
            ),
            (["or", "c=c", "d=d"], [], 0, ""),
        ],
        0,
        "",
    )
