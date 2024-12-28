"""
Process the wikitext to extract plain text.
See https://www.mediawiki.org/wiki/Help:Wikitext_examples for the syntax of wikitext.
"""

from __future__ import annotations

import json
import re
from jsonargparse import CLI
from tqdm import tqdm
from pathlib import Path

from src.file_loader import generate_items_from_jsonl, generate_items_from_jsonl_tar_gz
from src.html_parser import ExtractedContent, extract_contents_from_html
from src.content_formatter import contents_to_markdown

LEAD_SECTION = "__LEAD__"


def remove_references(content_list: list[ExtractedContent]) -> list[ExtractedContent]:
    filtered_content_list: list[ExtractedContent] = []
    for content in content_list:
        # If the content contains reference (e.g., "1. ↑ ..."), we should skip the rest of the contents
        # assuming that the rest of the contents are references and external links
        if content.tag_name == "ol" and re.search(r"\d+\. ↑", content.text):
            break
        filtered_content_list.append(content)
    return filtered_content_list


def remove_empty_headers(
    content_list: list[ExtractedContent],
) -> list[ExtractedContent]:
    if not content_list:
        return content_list

    header_tags = {"h3", "h4"}
    filter_contents: list[ExtractedContent] = []
    for i in range(len(content_list) - 1):
        if (
            content_list[i].tag_name in header_tags
            and content_list[i + 1].tag_name == content_list[i].tag_name
        ):
            continue
        filter_contents.append(content_list[i])

    if content_list[-1].tag_name not in filter_contents:
        filter_contents.append(content_list[-1])
    return filter_contents


def remove_empty_sections(
    content_list: list[ExtractedContent],
) -> list[ExtractedContent]:
    filtered_contents: list[ExtractedContent] = []

    current_contents: list[ExtractedContent] = []
    for content in content_list:
        # Update current_contents if it sees a new section
        if (
            current_contents
            and content.section_title != current_contents[0].section_title
        ):
            # add the contents only if the section contents contain non-header elements
            if any(c.tag_name not in {"h3", "h4"} for c in current_contents):
                filtered_contents += current_contents
            current_contents = []
        current_contents.append(content)

    if any(c.tag_name not in {"h3", "h4"} for c in current_contents):
        filtered_contents += current_contents
    return filtered_contents


def main(
    input_file: str, output_file: str, remove_refs: bool = True, debug: bool = False
):
    if input_file.endswith("tar.gz"):
        parse_input = generate_items_from_jsonl_tar_gz
    else:
        parse_input = generate_items_from_jsonl

    Path(output_file).parent.mkdir(exist_ok=True, parents=True)
    with open(output_file, "w") as f_out:
        for i, item in tqdm(enumerate(parse_input(input_file))):
            contents = extract_contents_from_html(item["article_body"]["html"])

            contents = remove_references(contents)
            contents = remove_empty_headers(contents)
            contents = remove_empty_sections(contents)

            text = contents_to_markdown(
                contents, title=item["name"], remove_refs=remove_refs
            )
            f_out.write(
                json.dumps({"text": text, "url": item["url"]}, ensure_ascii=False)
                + "\n"
            )

            if debug:
                Path("debug_htmls").mkdir(exist_ok=True)
                Path("debug_outputs").mkdir(exist_ok=True)
                with open(f"debug_htmls/{i:02}.html", "w") as f:
                    f.write(item["article_body"]["html"])

                with open(f"debug_outputs/{i:02}.md", "w") as f:
                    f.write(text)


if __name__ == "__main__":
    CLI(main)
