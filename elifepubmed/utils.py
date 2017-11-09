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
