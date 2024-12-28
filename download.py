from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Literal

import requests
from jsonargparse import CLI
from tqdm import tqdm


def download_file_with_progress(url: str, file_path: str | PathLike[str]):
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)
    with open(file_path, "wb") as file:
        for data in response.iter_content(1024):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR: Something went wrong")


def download_data(
    language: str,
    project: Literal[
        "wiki",
        "wiktionary",
        "wikibooks",
        "wikinews",
        "wikiquote",
        "wikisource",
        "wikiversity",
        "wikivoyage",
    ],
    date: str = "20241220",
    output_dir: str = "data_downloaded",
):
    filename = f"{language}{project}-NS0-{date}-ENTERPRISE-HTML.json.tar.gz"
    url = f"https://dumps.wikimedia.org/other/enterprise_html/runs/{date}/{filename}"

    Path(output_dir).mkdir(exist_ok=True, parents=True)
    save_path = Path(output_dir) / filename
    download_file_with_progress(url, save_path)


if __name__ == "__main__":
    CLI(download_data)
