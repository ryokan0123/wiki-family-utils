# Copyright 2023 Ryokan Ri (@ryokan0123)
# Changes made from the original (https://github.com/singletongue/wikipedia-utils) with the following license.
#
# Copyright 2022 Masatoshi Suzuki (@singletongue)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import annotations

import json
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal
from unicodedata import normalize

from bs4 import BeautifulSoup
from jsonargparse import CLI
from tqdm import tqdm

LEAD_SECTION = "__LEAD__"

# some parameters are tuned for Japanese texts
# please tweak them for your language
DEFAULT_TAGS_TO_REMOVE = ["table"]
DEFAULT_TAGS_TO_EXTRACT = ["p", "li", "h3", "h4"]
DEFAULT_INNER_TAGS_TO_REMOVE = [
    {"name": "sup"},
    {"name": "span", "attrs": {"class": "mw-editsection"}},
]
DEFAULT_SECTIONS_TO_IGNORE = ["脚注", "出典", "参考文献", "関連項目", "外部リンク"]
PHRASES_TO_IGNORE = ["このページはスタブ"]
ADHOC_REPLACE_MAP = {
    "IPA(?)": "IPA",
    "発音(?)": "発音",
}


def normalize_text(text: str) -> str:
    text = normalize("NFKC", text)
    text = " ".join(text.split())
    text = "".join(char for char in text if char.isprintable())
    text = text.strip()
    for before, after in ADHOC_REPLACE_MAP.items():
        text = text.replace(before, after)
    return text


def read_lines_from_tar_gz(file_path: str) -> Iterator[str]:
    with tarfile.open(file_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile():
                f = tar.extractfile(member)
                if f is not None:
                    for line in f:
                        yield line.decode("utf-8").strip()


@dataclass
class ExtractedContent:
    section_title: str
    text: str
    tag_name: str


def generate_contents_from_html(
    html_string: str,
    tags_to_extract: list[str] | None = None,
    tags_to_remove: list[str] | None = None,
    inner_tags_to_remove: list[dict[str, str]] | None = None,
) -> Iterator[ExtractedContent]:
    tags_to_extract = tags_to_extract or DEFAULT_TAGS_TO_EXTRACT
    tags_to_remove = tags_to_remove or DEFAULT_TAGS_TO_REMOVE
    inner_tags_to_remove = inner_tags_to_remove or DEFAULT_INNER_TAGS_TO_REMOVE

    soup = BeautifulSoup(html_string, "html.parser")

    section = soup.find(["section"])
    section_title = LEAD_SECTION
    text = ""
    while section:
        if section.h2 is not None:
            section_title = normalize_text(section.h2.text)

        for tag in section.find_all(tags_to_remove):
            tag.clear()

        for tag in section.find_all(tags_to_extract):
            for params in inner_tags_to_remove:
                for inner_tag in tag.find_all(**params):
                    inner_tag.clear()

            # special process to remove template text
            if any(phrase in tag.text for phrase in PHRASES_TO_IGNORE):
                continue
            text += normalize_text(tag.text)
            text = text.strip()
            if len(text) > 1:
                yield ExtractedContent(section_title, text, tag.name)
            text = ""

        section = section.find_next_sibling(["section"])


def process_contents_to_plain_text(content_list: list[ExtractedContent]) -> str:
    plain_text = ""
    current_section_title = LEAD_SECTION
    for content in content_list:
        if content.section_title != current_section_title:
            current_section_title = content.section_title
            plain_text += "\n## " + current_section_title + "\n"

        if content.tag_name == "li":
            plain_text += "- "
        plain_text += content.text + "\n"
    return plain_text.strip()


def process_contents_to_passages(
    content_list: list[ExtractedContent], max_num_characters: int
) -> Iterator[dict[str, str]]:
    current_passage = ""
    current_section_title = LEAD_SECTION
    for content in content_list:
        if (
            (
                len(current_passage) + len(content.text) > max_num_characters
            )  # the passage is full
            or content.section_title != current_section_title  # the section is changed
        ) and current_passage != "":  # the passage is not empty
            yield {"passage": current_passage, "section_title": current_section_title}
            current_passage = ""
        if content.section_title != current_section_title:
            current_section_title = content.section_title
        current_passage += content.text + "\n"
    if current_passage != "":
        yield {"passage": current_passage, "section_title": current_section_title}


def extract_data(
    data_path: str,
    output_type: Literal["plain_text", "passages"],
    output_path: str | None,
    passage_num_characters: int = 400,
    sections_to_ignore: list[str] | None = None,
    tags_to_extract: list[str] | None = None,
    tags_to_remove: list[str] | None = None,
    inner_tags_to_remove: list[dict[str, str]] | None = None,
):
    sections_to_ignore = sections_to_ignore or DEFAULT_SECTIONS_TO_IGNORE

    if output_path is None:
        output_path = Path(data_path).parent / (
            Path(data_path).stem.split(".")[0] + output_type + ".jsonl"
        )

    with open(output_path, "w") as f:
        for line in tqdm(read_lines_from_tar_gz(data_path)):
            json_data = json.loads(line)
            page_title = json_data["name"]
            content_list: list[ExtractedContent] = []
            for content in generate_contents_from_html(
                json_data["article_body"]["html"],
                tags_to_extract=tags_to_extract,
                tags_to_remove=tags_to_remove,
                inner_tags_to_remove=inner_tags_to_remove,
            ):
                if content.tag_name in sections_to_ignore:
                    continue
                content_list.append(content)

            if output_type == "plain_text":
                plain_text = process_contents_to_plain_text(content_list)
                item_dict = {
                    "title": page_title,
                    "text": plain_text,
                    "url": json_data["url"],
                }
                f.write(json.dumps(item_dict, ensure_ascii=False) + "\n")
            elif output_type == "passages":
                for passage_dict in process_contents_to_passages(
                    content_list, passage_num_characters
                ):
                    passage_dict.update({"title": page_title, "url": json_data["url"]})
                    f.write(json.dumps(passage_dict, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    CLI(extract_data)
