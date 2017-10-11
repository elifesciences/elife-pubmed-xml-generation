import unittest
import time
import os
from elifepubmed import generate
from elifepubmed.conf import config, parse_raw_config

TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
generate.TMP_DIR = TEST_BASE_PATH + "tmp" + os.sep

class TestGenerate(unittest.TestCase):

    def setUp(self):
        self.passes = []
        self.default_pub_date = time.strptime("2017-07-17 07:17:07", "%Y-%m-%d %H:%M:%S")
        self.passes.append(('elife-15743-v1.xml', 'elife-pubmed-15743-20170717071707.xml', 'elife', self.default_pub_date))
        self.passes.append(('elife_poa_e12717.xml', 'elife-pubmed-12717-20170717071707.xml', 'elife', self.default_pub_date))
        self.passes.append(('elife_poa_e00003.xml', 'elife-pubmed-00003-20170717071707.xml', 'elife', self.default_pub_date))
        self.passes.append(('elife-02935-v2.xml', 'elife-pubmed-02935-20170717071707.xml', 'elife', self.default_pub_date))
        self.passes.append(('elife-00666.xml', 'elife-pubmed-00666-20170717071707.xml', 'elife', self.default_pub_date))

    def read_file_content(self, file_name):
        fp = open(file_name, 'rb')
        content = fp.read()
        fp.close()
        return content

    def test_parse(self):
        for (article_xml_file, pubmed_xml_file, config_section, pub_date) in self.passes:
            file_path = TEST_DATA_PATH + article_xml_file
            articles = generate.build_articles_for_pubmed([file_path])
            pXML = generate.build_pubmed_xml(articles, config_section, pub_date, False)
            pubmed_xml = pXML.output_XML()
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
            # check the batch_id will be similar to the XML filename
            self.assertEqual(pXML.batch_id + '.xml', pubmed_xml_file)


    def test_pubmed_xml(self):
        "test at least one article through this function for test coverage"
        article_xml_file, pubmed_xml_file, config_section, pub_date = self.passes[0]
        file_path = TEST_DATA_PATH + article_xml_file
        articles = generate.build_articles_for_pubmed([file_path])
        pubmed_xml = generate.pubmed_xml(articles, config_section, pub_date, False)
        self.assertIsNotNone(pubmed_xml)


    def test_parse_do_no_pass_pub_date(self):
        """
        For test coverage build a PubMedXML object without passing in a pub_date
        and also test pretty output too for coverage
        """
        article_xml_file = 'elife-15743-v1.xml'
        file_path = TEST_DATA_PATH + article_xml_file
        articles = generate.build_articles_for_pubmed([file_path])
        raw_config = config['elife']
        pubmed_config = parse_raw_config(raw_config)
        pubmed_object = generate.PubMedXML(articles, pubmed_config, None, True)
        self.assertIsNotNone(pubmed_object.pub_date)
        self.assertIsNotNone(pubmed_object.generated)
        self.assertIsNotNone(pubmed_object.last_commit)
        self.assertIsNotNone(pubmed_object.comment)
        self.assertIsNotNone(pubmed_object.output_XML(pretty=True, indent='\t'))

    def test_pubmed_xml_to_disk(self):
        "test writing to disk for test coverage"
        article_xml_file = 'elife_poa_e00003.xml'
        pubmed_xml_file = 'elife-pubmed-00003-20170717071707.xml'
        config_section = 'elife'
        pub_date = self.default_pub_date
        file_path = TEST_DATA_PATH + article_xml_file
        # build the article object
        articles = generate.build_articles_for_pubmed([file_path])
        # generate and write to disk
        generate.pubmed_xml_to_disk(articles, config_section, pub_date, False)
        # check the output matches
        with open(TEST_DATA_PATH + pubmed_xml_file, 'rb') as fp:
            expected_output = fp.read()
        with open(generate.TMP_DIR + pubmed_xml_file, 'rb') as fp:
            generated_output = fp.read()
        self.assertEqual(generated_output, expected_output)

if __name__ == '__main__':
    unittest.main()
