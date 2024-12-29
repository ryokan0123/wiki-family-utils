from __future__ import annotations

import re

from src.html_parser import ExtractedContent

LEAD_SECTION = "__LEAD__"


def contents_to_markdown(
    content_list: list[ExtractedContent], title: str, remove_refs: bool
) -> str:
    """
    Convert the extracted contents to markdown format.
    """
    # Remove Reference section
    if remove_refs:
        filtered_content_list = []
        for content in content_list:
            # If the content contains reference (e.g., "1. ↑ ..."), we should skip the rest of the contents
            # assuming that the rest of the contents are references and external links
            if (
                remove_refs
                and content.tag_name == "ol"
                and re.search(r"\d+\. ↑", content.text)
            ):
                break
            filtered_content_list.append(content)
        content_list = filtered_content_list

    # if there is a section that only has header elements and no content, we should skip it
    section_with_contents = set()
    for content in content_list:
        if content.tag_name not in {"h3", "h4"}:
            section_with_contents.add(content.section_title)

    current_section = LEAD_SECTION
    text = "# " + title + "\n"
    li_count = 0
    for content in content_list:
        if content.section_title not in section_with_contents:
            continue
        if current_section != content.section_title:
            current_section = content.section_title
            text += f"\n## {current_section}\n\n"

        # Increase the list count if the tag is ordered list
        if content.tag_name == "li-ol":
            li_count += 1
        else:
            li_count = 0

        if content.tag_name == "table":
            text += "\n" + content.text + "\n\n"
        elif content.tag_name == "li-ul":
            text += f"* {content.text}\n"
        elif content.tag_name == "li-ol":
            text += f"{li_count}. {content.text}\n"
        elif content.tag_name == "h3":
            text += f"\n### {content.text}\n\n"
        elif content.tag_name == "h4":
            text += f"\n#### {content.text}\n\n"
        elif content.tag_name == "p":
            text += content.text + "\n"
        elif content.tag_name == "dt":
            text += f"**{content.text}**\n"
        elif content.tag_name == "dd":
            text += f"\n{content.text}\n\n"
        elif content.tag_name in {"ul", "ol"}:
            text += content.text + "\n"
        elif content.tag_name in {"img"}:
            text += content.text
        else:
            raise ValueError(f"Invalid tag name: {content.tag_name}")

    text = text.strip()
    # remove new lines that are more than 3
    text = re.sub(r"\n{3,}", "\n\n", text)
    # remove reference tags
    if remove_refs:
        text = re.sub(r"\[\^.+?\]", "", text)
    return text
