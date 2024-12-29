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


def _remove_unnecessary_elements(tag: Tag) -> None:
    for tag in tag.find_all(["div", "tr", "table", "sup", "ul", "span"]):
        if tag.name in {"div", "tr", "table"}:
            if set(tag.attrs.get("class", [])) & {
                "stub",
                "navbar",
                "navbox",
                "noprint",
                "boilerplate",
                "ambox",
                "infobox",
                "selfreference",
                "navbox-inner",
            }:
                tag.clear()
        elif tag.name == "sup":
            if set(tag.attrs.get("class", [])) & {"noprint"}:
                tag.clear()
        elif tag.name == "span":
            if set(tag.attrs.get("class", [])) & {"noprint"}:
                tag.clear()
        elif tag.name == "ul":
            if set(tag.attrs.get("class", [])) & {"gallery"}:
                tag.clear()

        if tag.attrs.get("role") == "presentation":
            tag.clear()


def _clean_up_tag_for_reference(tag: Tag, soup):
    # replace reference tag to markdown format
    for inner_tag in tag.find_all(name="sup", attrs={"class": "reference"}):
        if inner_tag.text.startswith("["):
            new_tag = soup.new_tag("p")
            new_tag.string = "[^" + inner_tag.text[1:]
            inner_tag.replace_with(new_tag)
        else:
            # there is irregular tag like ":95-96" in "ホームがある地下駅で[2]:95-96"
            inner_tag.clear()
    # replace linkback-text to "↑"
    for inner_tag in tag.find_all(name="span", attrs={"class": "mw-linkback-text"}):
        inner_tag.string = "↑ "


def _clean_up_tag_for_math(tag: Tag, soup) -> None:
    # Do not want to italicize by 'i' because it add redundant * to all the math marks.
    for inner_tag in tag.find_all(["i"]):
        inner_tag.replace_with(inner_tag.text)
    # Convert sup to latex-like style
    for inner_tag in tag.find_all(["sup"]):
        sup_string = f"^{inner_tag.text}"
        if len(inner_tag.text) > 1:
            sup_string = "^{" + inner_tag.text + "}"
        inner_tag.replace_with(sup_string)
    # Convert sub to latex-like style
    for inner_tag in tag.find_all(["sub"]):
        sub_string = f"_{inner_tag.text}"
        if len(inner_tag.text) > 1:
            sub_string = "_{" + inner_tag.text + "}"
        inner_tag.replace_with(sub_string)

    # convert math element properly
    for inner_tag in tag.find_all(name="span", attrs={"class": "mwe-math-element"}):
        assert inner_tag.annotation.text
        new_tag = soup.new_tag("p")
        new_tag.string = "$" + inner_tag.annotation.text + "$"
        inner_tag.replace_with(new_tag)


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
    _remove_unnecessary_elements(soup)

    section = soup.find(["section"])
    section_title = LEAD_SECTION
    content_list: list[ExtractedContent] = []
    text = ""
    while section:
        if section.h2 is not None:
            section_title = normalize_text(section.h2.text)

        for tag in section.find_all(["p", "h3", "h4", "table", "dt", "dd", "ul", "ol"]):
            # We cannot extract audio tags
            if tag.find("audio"):
                continue

            # avoid repeating nested bulltet points
            if tag.name in {"ul", "ol", "dl", "dd"}:
                if tag.find_parent(["ul", "ol"]):
                    continue

            _remove_unnecessary_elements_in_text_element(tag)
            _clean_up_tag_for_reference(tag, soup)
            _clean_up_tag_for_math(tag, soup)

            # remove image
            for inner_tag in tag.find_all(name="img"):
                inner_tag.decompose()

            if tag.name == "table":
                # patch for the table tag
                # markdownify does not add a necessary new line between caption and table
                # so we need to add it manually
                caption = tag.find("caption")
                if caption is not None:
                    caption.string = f"{caption.text}\n"
                text += markdownify(str(tag), strip=["a"], escape_underscores=False)
            elif tag.name == "ul" or tag.name == "ol":
                text += markdownify(
                    str(tag), strip=["a"], escape_underscores=False
                ).strip()
            else:
                text += normalize_text(tag.text)

            text = text.strip()
            if len(text) > 1:
                content_list.append(ExtractedContent(section_title, text, tag.name))
            text = ""

        section = section.find_next_sibling(["section"])
    return content_list
