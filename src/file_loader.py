import json
from typing import Any, Iterator
import tarfile


def generate_items_from_jsonl(file_path: str) -> Iterator[dict[str, Any]]:
    with open(file_path, "r") as f:
        for line in f:
            yield json.loads(line)


def generate_items_from_jsonl_tar_gz(file_path: str) -> Iterator[dict[str, Any]]:
    with tarfile.open(file_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile():
                f = tar.extractfile(member)
                if f is not None:
                    for line in f:
                        yield json.loads(line.decode("utf-8"))
