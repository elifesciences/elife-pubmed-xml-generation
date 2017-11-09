import unittest
from elifepubmed import utils

class TestUtils(unittest.TestCase):

    def test_allowed_tags(self):
        self.assertIsNotNone(utils.allowed_tags(), 'allowed_tags not returned')

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

if __name__ == '__main__':
    unittest.main()
