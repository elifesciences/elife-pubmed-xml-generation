import unittest
import time
import os
from elifepubmed import generate

TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
generate.TMP_DIR = TEST_BASE_PATH + "tmp" + os.sep

class TestGenerate(unittest.TestCase):

    def setUp(self):
        self.passes = []
        self.default_pub_date = time.strptime("2017-07-17 07:17:07", "%Y-%m-%d %H:%M:%S")
        self.passes.append(('elife-15743-v1.xml', 'elife-2016-05-13-143615-PubMed.xml', 'elife', self.default_pub_date))

    def read_file_content(self, file_name):
        fp = open(file_name, 'rb')
        content = fp.read()
        fp.close()
        return content

    def test_parse(self):
        for (article_xml_file, pubmed_xml_file, config_section, pub_date) in self.passes:
            file_path = TEST_DATA_PATH + article_xml_file
            articles = generate.build_articles_for_pubmed([file_path])
            pubmed_xml = generate.pubmed_xml(articles, config_section, pub_date, False)
            model_pubmed_xml = self.read_file_content(TEST_DATA_PATH + pubmed_xml_file)

            # debug to get some test artifacts
            """
            print "pubmed_xml"
            print pubmed_xml
            print " "
            print "model_pubmed_xml"
            print model_pubmed_xml
            """

            self.assertEqual(pubmed_xml, model_pubmed_xml)


if __name__ == '__main__':
    unittest.main()
