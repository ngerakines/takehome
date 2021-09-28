import abc
import csv
import io
import os
from typing import Optional, Dict, Any, List, Tuple

QUOTE = '"'
SPACE = " "
OPEN = "("
CLOSE = ")"

stack = Tuple[List[str], List["stack"], int, str]


class IndexedFile:
    def __init__(
        self,
        location: str,
        scanned: bool = False,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
        file_name: Optional[str] = None,
    ):
        self.location = location
        self.scanned = scanned
        self._file_size: Optional[int] = file_size
        self._content_type: Optional[str] = content_type
        self._file_name: Optional[str] = file_name

    def scan(self):
        if self.scanned:
            return

        stats = os.stat(self.location)
        self._file_size = stats.st_size

        _, self._file_name = os.path.split(self.location)

        self._content_type = "application/octet-stream"
        self.scanned = True

    @property
    def file_size(self):
        self.scan()
        if self._file_size is None:
            raise ValueError("unable to determine file size")
        return self._file_size

    @property
    def content_type(self):
        self.scan()
        if self._content_type is None:
            raise ValueError("unable to determine content type")
        return self._content_type

    @property
    def file_name(self):
        self.scan()
        if self._file_name is None:
            raise ValueError("unable to determine file name")
        return self._file_name

    def __eq__(self, other):
        return isinstance(other, IndexedFile) and self.location == other.location

    def __hash__(self):
        return hash(self.location)


class Index:
    def __init__(self):
        self.files: Dict[str, IndexedFile] = {}

    def add(self, location: str, scan: bool = False):
        indexed_file = IndexedFile(location)
        if scan:
            indexed_file.scan()
        self.files[location] = indexed_file

    def csv_out(self, dest: Any):
        writer = csv.DictWriter(
            dest, fieldnames=["location", "file_name", "file_size", "content_type"]
        )
        writer.writeheader()
        for location in sorted(self.files.keys(), reverse=True):
            file = self.files[location]
            writer.writerow(
                {
                    "location": file.location,
                    "file_name": file.file_name,
                    "file_size": file.file_size,
                    "content_type": file.content_type,
                }
            )

    def to_file(self, location: str):
        with open(location, "w") as dest:
            self.csv_out(dest)

    def to_string(self) -> str:
        output = io.StringIO()
        self.csv_out(output)
        return output.getvalue()

    def load_file(self, location: str):
        with open(location, "r") as source:
            reader = csv.DictReader(source)
            for row in reader:
                self.files[row["location"]] = IndexedFile(
                    location=row["location"],
                    scanned=True,
                    file_name=row["file_name"],
                    content_type=row["content_type"],
                    file_size=int(row["file_size"]),
                )

    def search(self, query: str) -> List[str]:
        results: List[str] = []

        matcher = parse_query(query)
        for indexed_file in self.files.values():
            if matcher.match(indexed_file):
                results.append(indexed_file.location)

        return results


class Indexer:
    def __init__(self, index: Optional[Index] = None):
        self.index = index
        if self.index is None:
            self.index = Index()

    def scan_directory(self, directory: str, scan: bool = False):
        for root, directories, files in os.walk(
            directory, topdown=False, followlinks=False
        ):
            for file in files:
                self.index.add(os.path.join(root, file), scan=scan)


class Matcher(abc.ABC):
    @abc.abstractmethod
    def match(self, indexed_file: IndexedFile) -> bool:
        pass


class TrueMatcher(Matcher):
    def match(self, indexed_file: IndexedFile) -> bool:
        return True

    def __str__(self):
        return "TrueMatcher()"


class FalseMatcher(Matcher):
    def match(self, indexed_file: IndexedFile) -> bool:
        return False

    def __str__(self):
        return "FalseMatcher()"


class AndMatcher(Matcher):
    def __init__(self, elements: List[Matcher]) -> None:
        self.elements = elements
        super().__init__()

    def match(self, indexed_file: IndexedFile) -> bool:
        if len(self.elements) == 0:
            return False
        return all(el.match(indexed_file) for el in self.elements)

    def __str__(self):
        return "AndMatcher(elements={elements})".format(
            elements=",".join([str(el) for el in self.elements])
        )


class OrMatcher(Matcher):
    def __init__(self, elements: List[Matcher]) -> None:
        self.elements = elements
        super().__init__()

    def match(self, indexed_file: IndexedFile) -> bool:
        if len(self.elements) == 0:
            return False
        return any(el.match(indexed_file) for el in self.elements)

    def __str__(self):
        return "OrMatcher(elements={elements})".format(
            elements=",".join([str(el) for el in self.elements])
        )


class FileNameMatcher(Matcher):
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        super().__init__()

    def match(self, indexed_file: IndexedFile) -> bool:
        return self.file_name == indexed_file.file_name

    def __str__(self):
        return f"FileNameMatcher({self.file_name})"


class FileSizeMatcher(Matcher):
    def __init__(self, file_size: int) -> None:
        self.file_size = file_size
        super().__init__()

    def match(self, indexed_file: IndexedFile) -> bool:
        return self.file_size == indexed_file.file_size

    def __str__(self):
        return f"FileSizeMatcher({self.file_size})"


class ContentTypeMatcher(Matcher):
    def __init__(self, content_type: str) -> None:
        self.content_type = content_type
        super().__init__()

    def match(self, indexed_file: IndexedFile) -> bool:
        return self.content_type == indexed_file.content_type

    def __str__(self):
        return f"ContentTypeMatcher({self.content_type})"


def parse_query(query: str) -> Matcher:
    parsed_stack = scrub_stack(parse_nested_tokens(query))
    if parsed_stack is None:
        raise ValueError(f"invalid query: {query}")

    return matcher_from_stack(parsed_stack[0], parsed_stack[1])


def matcher_from_stack(tokens: List[str], children: List["stack"]) -> Matcher:
    matchers: List[Matcher] = []
    matchers_op = "and"

    if "or" in tokens:
        matchers_op = "or"

    for token in tokens:
        if token == "or":
            matchers_op = "or"
        token_parts = token.split("=", 2)
        if token_parts[0] == "file_name":
            matchers.append(FileNameMatcher(token_parts[1]))
        elif token_parts[0] == "file_size":
            matchers.append(FileSizeMatcher(int(token_parts[1])))
        elif token_parts[0] == "content_type":
            matchers.append(ContentTypeMatcher(token_parts[1]))

    for child in children:
        matchers.append(matcher_from_stack(child[0], child[1]))

    if matchers_op == "or":
        return OrMatcher(elements=matchers)

    return AndMatcher(elements=matchers)


def parse_nested_tokens(value: str, start: int = -1, depth: int = 0) -> stack:
    buffer = ""
    current_stack = ([], [], 0, "")
    inside_quote = False
    for index, char in enumerate(value):
        if index <= start:
            continue

        if char == OPEN:
            child_stack = parse_nested_tokens(value[index:], start=0, depth=depth + 1)
            current_stack[1].append(child_stack)
            start = index + child_stack[2]
            continue

        elif char == CLOSE:
            if len(buffer) > 0:
                current_stack[0].append(buffer)

            return current_stack[0], current_stack[1], index, value[index + 1 :]

        if char == SPACE and not inside_quote:
            current_stack[0].append(buffer)
            buffer = ""
        elif char == QUOTE and not inside_quote:
            inside_quote = True
        elif char == QUOTE and inside_quote:
            inside_quote = False
        else:
            buffer += char

    if len(buffer) > 0:
        current_stack[0].append(buffer)

    return current_stack


def scrub_stack(value: stack) -> Optional[stack]:
    tokens = value[0]

    children = list(map(lambda c: scrub_stack(c), value[1]))
    children = list(filter(None, children))

    tokens = list(filter(None, tokens))

    if len(tokens) == 0 and len(children) == 0:
        return None

    return tokens, children, 0, ""
