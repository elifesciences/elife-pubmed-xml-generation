import re
from collections import OrderedDict
from elifetools import utils as etoolsutils
from elifearticle import utils as eautils


TAG_REPLACEMENT_MAP = OrderedDict(
    [
        ("italic", "i"),
        ("bold", "b"),
        ("underline", "u"),
    ]
)


def allowed_tags():
    "tuple of whitelisted tags"
    return (
        "<i>",
        "</i>",
        "<italic>",
        "</italic>",
        "<b>",
        "</b>",
        "<bold>",
        "</bold>",
        "<sup>",
        "</sup>",
        "<sub>",
        "</sub>",
        "<u>",
        "</u>",
        "<underline>",
        "</underline>",
        "<p>",
        "</p>",
    )


def allowed_tag_names():
    "only tag names of allow_tags sorted with no duplicates"
    # note: uses set comprehension syntax when removing duplicate values
    return list(sorted({re.sub(r"[<>/]", "", tag) for tag in allowed_tags()}))


def replace_mathml_tags(string, replacement="[Formula: see text]"):
    if not string:
        return string
    # match over newlines with DOTALL for kitchen sink testing and if found in real articles
    for tag_match in re.finditer(
        r"<inline-formula>(.*?)</inline-formula>", string, re.DOTALL
    ):
        tag_content = tag_match.group(1)
        old_tag = "<inline-formula>" + tag_content + "</inline-formula>"
        string = string.replace(old_tag, replacement)
    return string


def replace_inline_tags(string, tag_map=None):
    """Pubmed allows <i> tags, not <italic> tags, replace them"""
    if not tag_map:
        tag_map = TAG_REPLACEMENT_MAP
    for from_tag, to_tag in tag_map.items():
        string = eautils.replace_tags(string, from_tag, to_tag)
    return string


def compare_values(value1, value2, case_sensitive):
    "compare non None value1 and value2 in case sensitive or case insensitive"
    if not value1 or not value2:
        return None
    if case_sensitive:
        return bool(value1 == value2)
    # default case insensitive matching
    return bool(value1.lower() == value2.lower())


def pubmed_publication_type(article_type, display_channel, types_map):
    "use the publication_types map to determine which PubMed value"
    if types_map:
        for match in types_map:
            # return the first match that matches all the required values
            # if there is not publication_type then skip the match
            if not match.get("publication_type"):
                continue
            match_count = 0
            match_count_required = None
            # how many elements must we match on to return a value
            if match.get("article_type") and match.get("display_channel"):
                match_count_required = 2
            elif match.get("article_type") or match.get("display_channel"):
                match_count_required = 1
            # look for matches
            if (
                compare_values(
                    match.get("article_type"), article_type, match.get("case_sensitive")
                )
                is True
            ):
                match_count = match_count + 1
            if (
                compare_values(
                    match.get("display_channel"),
                    display_channel,
                    match.get("case_sensitive"),
                )
                is True
            ):
                match_count = match_count + 1
            # final check to return
            if match_count == match_count_required:
                return match.get("publication_type")
    # default
    return "Journal Article"


def contributor_initials(surname, given_name):
    "a simple author initials format"
    return "".join([value[0] for value in [given_name, surname] if value is not None])


def join_phrases(phrase_list, glue_one=", ", glue_two=" "):
    "join a list of phrases together with commas unless there is already punctuation"
    phrase_text = ""
    for phrase in phrase_list:
        if not phrase:
            continue
        # add a comma if the text does not end in punctuation already
        if phrase_text != "" and phrase_text.endswith("."):
            # join with a space as glue
            phrase_text = "".join([phrase_text, glue_two, phrase])
        elif phrase_text != "":
            # join with a comma space as glue
            phrase_text = "".join([phrase_text, glue_one, phrase])
        elif phrase_text == "":
            phrase_text = phrase
    return phrase_text


def abstract_part_label(string, label_types):
    "look for a label for part of an abstract and return the string without the label"
    label = ""
    if string.lstrip().startswith("<bold>"):
        for tag_match in re.finditer(
            r"^<bold>(.*?)</bold>.*$", string.lstrip(), re.MULTILINE
        ):
            matched = tag_match.group(1)
            if matched.rstrip() in label_types:
                first_section = "<bold>{matched}</bold>".format(matched=matched)
                label = tag_match.group(1).rstrip(": ")
                # to support multiple lines, just strip the first_section from the original string
                string = string.split(first_section)[-1]
    return label, string


def abstract_paragraph(string, label_types):
    "parse an abstract paragraph into section data"
    part = OrderedDict()
    label, string = abstract_part_label(string, label_types)
    text = string.replace("</p>", "")
    if text != "":
        part["text"] = text
        part["label"] = label
    return part


def abstract_sec_parts(string):
    label = ""
    if string:
        parts = re.split(r".*?<title>(.*?)</title>", string)
        label = parts[1]
        string = parts[2]
    return label, string


def abstract_sec(string):
    "parse an abstract sec tag into section data"
    part = OrderedDict()
    label, string = abstract_sec_parts(string)
    string = etoolsutils.remove_tag("p", string)
    string = etoolsutils.remove_tag("sec", string)
    string = string.rstrip()
    if string != "":
        part["text"] = string
        part["label"] = label
    return part


def abstract_parts(abstract, label_types):
    "break apart an abstract into sections with optional labels"
    parts = []
    if not abstract:
        return parts
    # check for structured abstract
    if "<sec" in abstract and "<title" in abstract:
        for a_sec in abstract.split("<sec"):
            part = abstract_sec(a_sec)
            if part:
                parts.append(part)
    else:
        for a_section in abstract.split("<p>"):
            part = abstract_paragraph(a_section, label_types)
            if part:
                parts.append(part)
    return parts
