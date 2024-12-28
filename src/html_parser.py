from dataclasses import dataclass
import unicodedata
from typing import Literal

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

LEAD_SECTION = "__LEAD__"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = " ".join(text.split())
    text = "".join(char for char in text if char.isprintable())
    text = text.strip()
    return text


@dataclass
class ExtractedContent:
    section_title: str
    text: str
    tag_name: Literal["p", "h3", "h4", "table", "li-ul", "li-ol", "dt", "dd"]

    def __post_init__(self):
        if self.tag_name not in {
            "p",
            "h3",
            "h4",
            "table",
            "li-ul",
            "li-ol",
            "dt",
            "dd",
            "ul",
            "ol",
        }:
            raise ValueError(f"Invalid tag name: {self.tag_name}")


def _remove_unnecessary_elements_in_section(tag: Tag) -> None:
    for tag in tag.find_all(["table"]):
        # remove unnecessary boxes
        if any(
            c in tag.attrs.get("class", [])
            for c in ["ambox", "infobox", "selfreference"]
        ):
            tag.clear()
        # remove stub boxes
        if tag.attrs.get("role") == "presentation":
            tag.clear()

    # delete all stub, navbar, navbox
    for tag in tag.find_all(["div", "tr"]):
        if any(
            c in tag.attrs.get("class", [])
            for c in ["stub", "navbar", "navbox", "noprint", "boilerplate"]
        ):
            tag.clear()


def _remove_unnecessary_elements_in_text_element(tag: Tag) -> None:
    # remove redundant tags
    for params_to_clear in [
        {"name": "span", "attrs": {"class": "mw-editsection"}},
    ]:
        for inner_tag in tag.find_all(**params_to_clear):
            inner_tag.clear()
    # remove small characters like IPA<small>(?)</small>
    for inner_tag in tag.find_all(["small", "sup"]):
        if inner_tag.text == "(?)":
            inner_tag.clear()


def extract_contents_from_html(html_string: str) -> list[ExtractedContent]:
    """
    Extract block elements containing text from the HTML string.
    """
    soup = BeautifulSoup(html_string, "html.parser")

    section = soup.find(["section"])
    section_title = LEAD_SECTION
    content_list: list[ExtractedContent] = []
    text = ""
    while section:
        if section.h2 is not None:
            section_title = normalize_text(section.h2.text)

        _remove_unnecessary_elements_in_section(section)

        for tag in section.find_all(["p", "h3", "h4", "table", "dt", "dd", "ul", "ol"]):
            # We cannot extract audio tags
            if tag.find("audio"):
                continue

            # avoid repeating nested bulltet points
            if tag.name in {"ul", "ol", "dl", "dd"}:
                if tag.find_parent(["ul", "ol"]):
                    continue

            _remove_unnecessary_elements_in_text_element(tag)

            # replace reference tag to markdown format
            for inner_tag in tag.find_all(name="sup", attrs={"class": "reference"}):
                if inner_tag.text.startswith("["):
                    inner_tag.string = "[^" + inner_tag.text[1:]
                else:
                    # there is irregular tag like ":95-96" in "ホームがある地下駅で[2]:95-96"
                    inner_tag.clear()
            # replace linkback-text to "↑"
            for inner_tag in tag.find_all(
                name="span", attrs={"class": "mw-linkback-text"}
            ):
                inner_tag.string = "↑ "

            # convert the tag element to markdown text
            if tag.name == "table":
                # patch for the table tag
                # markdownify does not add a necessary new line between caption and table
                # so we need to add it manually
                caption = tag.find("caption")
                if caption is not None:
                    caption.string = f"{caption.text}\n"

                text += markdownify(str(tag), strip=["a"])
            elif tag.name == "ul" or tag.name == "ol":
                text += markdownify(str(tag), strip=["a"]).strip()
            else:
                text += normalize_text(tag.text)

            text = text.strip()
            if len(text) > 1:
                content_list.append(ExtractedContent(section_title, text, tag.name))
            text = ""

        section = section.find_next_sibling(["section"])
    return content_list
