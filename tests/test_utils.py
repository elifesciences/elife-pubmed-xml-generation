import unittest
from elifepubmed import utils
from collections import OrderedDict

class TestUtils(unittest.TestCase):

    def test_allowed_tags(self):
        self.assertIsNotNone(utils.allowed_tags(), 'allowed_tags not returned')

    def test_allowed_tag_names(self):
        self.assertEqual(utils.allowed_tag_names(),
                         ['b', 'bold', 'i', 'italic', 'p', 'sub', 'sup', 'u', 'underline'])

    def test_replace_mathml_tags(self):
        self.assertEqual(
            utils.replace_mathml_tags(None), None)
        self.assertEqual(
            utils.replace_mathml_tags('test'), 'test')
        self.assertEqual(
            utils.replace_mathml_tags(
                '<inline-formula><mml:math>m</mml:math></inline-formula>'),
                '[Formula: see text]')
        self.assertEqual(
            utils.replace_mathml_tags(
                '<inline-formula><mml:math>m</mml:math></inline-formula><inline-formula></inline-formula>'),
                '[Formula: see text][Formula: see text]')
        # test newline matches
        self.assertEqual(
            utils.replace_mathml_tags(
                "\n<inline-formula>\n\n<mml:math>m</mml:math>\n</inline-formula>\n"),
                "\n[Formula: see text]\n")

    def test_compare_values(self):
        "various comparisons of values"
        self.assertIsNone(utils.compare_values(None, None, None))
        self.assertIsNone(utils.compare_values(None, None, True))
        self.assertTrue(utils.compare_values('A', 'A', True))
        self.assertTrue(utils.compare_values('a', 'A', False))
        self.assertFalse(utils.compare_values('A', 'a', True))
        self.assertFalse(utils.compare_values('a', 'b', False))

    def test_pubmed_publication_type(self):
        "example of publication type matching normally loaded from the yaml file"
        # test 1, no values, return the default
        article_type = None
        display_channel = None
        types_map = None
        self.assertEqual(utils.pubmed_publication_type(
            article_type, display_channel, types_map), 'Journal Article')
        # test 2, article_type and no publciation_type
        article_type = 'research-article'
        display_channel = None
        types_map = [{
            'article_type': 'research-article'
        }]
        self.assertEqual(utils.pubmed_publication_type(
            article_type, display_channel, types_map), 'Journal Article')
        # test 3, article_type match only
        article_type = 'correction'
        display_channel = None
        types_map = [{
            'article_type': 'correction',
            'publication_type': 'Published Erratum'
        }]
        self.assertEqual(utils.pubmed_publication_type(
            article_type, display_channel, types_map), 'Published Erratum')
        # test 4, article_type and display_channel match
        article_type = 'correction'
        display_channel = 'Insight'
        types_map = [{
            'article_type': 'correction',
            'display_channel': 'insight',
            'publication_type': 'Editorial'
        }]
        self.assertEqual(utils.pubmed_publication_type(
            article_type, display_channel, types_map), 'Editorial')
        # test 5, article_type and display_channel match case sensitive
        article_type = 'correction'
        display_channel = 'Insight'
        types_map = [{
            'article_type': 'correction',
            'display_channel': 'Insight',
            'case_sensitive': True,
            'publication_type': 'Editorial'
        }]
        self.assertEqual(utils.pubmed_publication_type(
            article_type, display_channel, types_map), 'Editorial')
        # test 6, case sensitive with no matches returns the default
        article_type = 'correction'
        display_channel = 'insight'
        types_map = [{
            'article_type': 'correction',
            'display_channel': 'Insight',
            'case_sensitive': True,
            'publication_type': 'Editorial'
        }]
        self.assertEqual(utils.pubmed_publication_type(
            article_type, display_channel, types_map), 'Journal Article')


    def test_contributor_initials(self):
        "various contributor initial values to test"
        self.assertEqual(utils.contributor_initials(None, None), '')
        self.assertEqual(utils.contributor_initials('Ju', 'Young Seok'), 'YJ')
        self.assertEqual(utils.contributor_initials('Ju', None), 'J')


    def test_join_phrases(self):
        "test joining some phrases with punctuation"
        self.assertEqual(utils.join_phrases([None, None]), '')
        self.assertEqual(utils.join_phrases(['A', 'B', 'C']), 'A, B, C')
        self.assertEqual(utils.join_phrases(['A', 'B.', 'C']), 'A, B. C')


    def test_abstract_sections(self):
        "test splitting abstract content into sections"
        self.assertEqual(utils.abstract_sections(None), [])
        self.assertEqual(utils.abstract_sections(
            '<p>First.</p><p>Second.</p>'),
            [
                OrderedDict([
                    ('text', 'First.'),
                    ('label', '')
                    ]),
                OrderedDict([
                    ('text', 'Second.'),
                    ('label', '')
                    ]),
                ]
            )


if __name__ == '__main__':
    unittest.main()
