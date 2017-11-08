
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

def contributor_initials(surname, given_name):
    "a simple author initials format"
    return ''.join([value[0] for value in [given_name, surname] if value is not None])
