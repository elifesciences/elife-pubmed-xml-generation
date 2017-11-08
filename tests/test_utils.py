import unittest
from elifepubmed import utils

class TestUtils(unittest.TestCase):

    def test_allowed_tags(self):
        self.assertIsNotNone(utils.allowed_tags(), 'allowed_tags not returned')

    def test_contributor_initials(self):
        "various contributor initial values to test"
        self.assertEqual(utils.contributor_initials(None, None), '')
        self.assertEqual(utils.contributor_initials('Ju', 'Young Seok'), 'YJ')
        self.assertEqual(utils.contributor_initials('Ju', None), 'J')


if __name__ == '__main__':
    unittest.main()
