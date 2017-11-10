import re

def allowed_tags():
    "tuple of whitelisted tags"
    return (
        '<i>', '</i>',
        '<italic>', '</italic>',
        '<b>', '</b>',
        '<bold>', '</bold>',
        '<sup>', '</sup>',
        '<sub>', '</sub>',
        '<u>', '</u>',
        '<underline>', '</underline>',
        '<b>', '</b>',
        '<bold>', '</bold>',
        '<p>', '</p>'
    )

def replace_mathml_tags(string, replacement="[Formula: see text]"):
    if not string:
        return string
    # match over newlines with DOTALL for kitchen sink testing and if found in real articles
    for tag_match in re.finditer("<inline-formula>(.*?)</inline-formula>", string, re.DOTALL):
        tag_content = tag_match.group(1)
        old_tag = '<inline-formula>' + tag_content + '</inline-formula>'
        string = string.replace(old_tag, replacement)
    return string


def compare_values(value1, value2, case_sensitive):
    "compare non None value1 and value2 in case sensitive or case insensitive"
    if not value1 or not value2:
        return None
    if case_sensitive:
        return bool(value1 == value2)
    else:
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
            if (compare_values(match.get("article_type"), article_type,
                               match.get("case_sensitive")) is True):
                match_count = match_count + 1
            if (compare_values(match.get("display_channel"), display_channel,
                               match.get("case_sensitive")) is True):
                match_count = match_count + 1
            # final check to return
            if match_count == match_count_required:
                return match.get("publication_type")
    # default
    return "Journal Article"

def contributor_initials(surname, given_name):
    "a simple author initials format"
    return ''.join([value[0] for value in [given_name, surname] if value is not None])
