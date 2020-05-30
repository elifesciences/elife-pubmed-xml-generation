import unittest
import time
import os
from xml.etree.ElementTree import Element
from xml.etree import ElementTree
from elifearticle.article import Article, Dataset
from elifepubmed import generate
from elifepubmed.conf import config, parse_raw_config


TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
generate.TMP_DIR = TEST_BASE_PATH + "tmp" + os.sep


def read_file_content(file_name):
    with open(file_name, 'rb') as open_file:
        return open_file.read()


class TestGenerate(unittest.TestCase):

    def setUp(self):
        self.passes = []
        self.default_pub_date = time.strptime("2017-07-17 07:17:07", "%Y-%m-%d %H:%M:%S")
        self.passes.append(
            ('elife-15743-v1.xml', 'elife-pubmed-15743-20170717071707.xml',
             'elife', self.default_pub_date))
        self.passes.append(
            ('elife_poa_e12717.xml', 'elife-pubmed-12717-20170717071707.xml',
             'elife', self.default_pub_date))
        self.passes.append(
            ('elife_poa_e00003.xml', 'elife-pubmed-00003-20170717071707.xml',
             'elife', self.default_pub_date))
        self.passes.append(
            ('elife-02935-v2.xml', 'elife-pubmed-02935-20170717071707.xml',
             'elife', self.default_pub_date))
        self.passes.append(
            ('elife-00666.xml', 'elife-pubmed-00666-20170717071707.xml',
             'elife', self.default_pub_date))
        self.passes.append(
            ('bmjopen-4-e003269.xml', 'pubmed-bmjopen-2013-003269-20170717071707.xml',
             'bmjopen', self.default_pub_date))
        self.passes.append(
            ('pb369-jats.xml', 'pb-pubmed-369-20170717071707.xml',
             'pb', self.default_pub_date))

    def test_parse(self):
        for (article_xml_file, pubmed_xml_file, config_section, pub_date) in self.passes:
            file_path = TEST_DATA_PATH + article_xml_file
            articles = generate.build_articles_for_pubmed(
                article_xmls=[file_path], config_section=config_section)
            p_xml = generate.build_pubmed_xml(articles, config_section, pub_date, False)
            pubmed_xml = str(p_xml.output_xml())
            model_pubmed_xml = str(
                read_file_content(TEST_DATA_PATH + pubmed_xml_file))
            self.assertEqual(pubmed_xml, model_pubmed_xml)
            # check the batch_id will be similar to the XML filename
            self.assertEqual(p_xml.batch_id + '.xml', pubmed_xml_file)

    def test_pubmed_xml(self):
        "test at least one article through this function for test coverage"
        article_xml_file = 'elife-15743-v1.xml'
        config_section = 'elife'
        pub_date = self.default_pub_date
        file_path = TEST_DATA_PATH + article_xml_file
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section)
        pubmed_xml = generate.pubmed_xml(articles, config_section, pub_date, False)
        self.assertIsNotNone(pubmed_xml)

    def test_parse_do_no_pass_pub_date(self):
        """
        For test coverage build a PubMedXML object without passing in a pub_date
        and also test pretty output too for coverage
        """
        article_xml_file = 'elife-15743-v1.xml'
        file_path = TEST_DATA_PATH + article_xml_file
        config_section = 'elife'
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section)
        raw_config = config[config_section]
        pubmed_config = parse_raw_config(raw_config)
        pubmed_object = generate.PubMedXML(articles, pubmed_config, None, True)
        self.assertIsNotNone(pubmed_object.pub_date)
        self.assertIsNotNone(pubmed_object.generated)
        self.assertIsNotNone(pubmed_object.last_commit)
        self.assertIsNotNone(pubmed_object.comment)
        self.assertIsNotNone(pubmed_object.output_xml(pretty=True, indent='\t'))

    def test_pubmed_xml_to_disk(self):
        "test writing to disk for test coverage"
        article_xml_file = 'elife_poa_e00003.xml'
        pubmed_xml_file = 'elife-pubmed-00003-20170717071707.xml'
        config_section = 'elife'
        pub_date = self.default_pub_date
        file_path = TEST_DATA_PATH + article_xml_file
        # build the article object
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section)
        # generate and write to disk
        generate.pubmed_xml_to_disk(articles, config_section, pub_date, False)
        # check the output matches
        with open(TEST_DATA_PATH + pubmed_xml_file, 'rb') as file_p:
            expected_output = file_p.read()
        with open(generate.TMP_DIR + pubmed_xml_file, 'rb') as file_p:
            generated_output = file_p.read()
        self.assertEqual(generated_output, expected_output)

    def test_set_is_poa(self):
        "test a method to make a non-eLife article aheadofprint by setting is_poa"
        article_xml_file = 'pb369-jats.xml'
        file_path = TEST_DATA_PATH + article_xml_file
        config_section = 'pb'
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section)
        # set the is_poa value
        articles[0].is_poa = True
        pubmed_xml = str(generate.pubmed_xml(articles, config_section))
        self.assertTrue('<PubDate PubStatus="aheadofprint">' in pubmed_xml,
                        'aheadofprint date not found in PubMed XML after setting is_poa')


class TestDataset(unittest.TestCase):

    def test_dataset_details_empty(self):
        """test an empty Dataset object"""
        dataset = Dataset()
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertIsNone(assigning_authority)
        self.assertIsNone(id_value)

    def test_dataset_details_doi(self):
        """test Dataset that has a doi"""
        doi = 'doi'
        dataset = Dataset()
        dataset.doi = doi
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertIsNone(assigning_authority)
        self.assertEqual(id_value, doi)

    def test_dataset_details_accession_id(self):
        """test Dataset that has a accession_id"""
        accession_id = 'accession_id'
        dataset = Dataset()
        dataset.accession_id = accession_id
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertIsNone(assigning_authority)
        self.assertEqual(id_value, accession_id)

    def test_dataset_details_both(self):
        """test Dataset that has both a doi and accession_id"""
        uri = 'www.ncbi.nlm.nih.gov/geo'
        doi = 'doi'
        accession_id = 'accession_id'
        expected_authority_value = 'NCBI:geo'
        dataset = Dataset()
        dataset.uri = uri
        dataset.doi = doi
        dataset.accession_id = accession_id
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertEqual(assigning_authority, expected_authority_value)
        self.assertEqual(id_value, doi)


class TestDatasetAssigningAuthority(unittest.TestCase):

    def test_dataset_assigning_authority_none(self):
        """dataset assigning authority when None"""
        assigning_authority = generate.dataset_assigning_authority(None)
        self.assertIsNone(assigning_authority)

    def test_dataset_assigning_authority_ncbi_geo(self):
        """dataset assigning authority for NCBI geo"""
        uri = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE48760'
        expected = 'NCBI:geo'
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)

    def test_dataset_assigning_authority_ncbi_dbgap(self):
        """NCBI dbgap"""
        uri = 'https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs001660.v1.p1'
        expected = 'NCBI:dbgap'
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)

    def test_dataset_assigning_authority_ncbi_nucleotide(self):
        """NCBI nucleotide"""
        uri = 'https://www.ncbi.nlm.nih.gov/nuccore/KY616976'
        expected = 'NCBI:nucleotide'
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)

    def test_dataset_assigning_authority_ncbi_sra(self):
        """NCBI sra"""
        uri = 'https://www.ncbi.nlm.nih.gov/sra/?term=SRA012474'
        expected = 'NCBI:sra'
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)


class TestPlainLanguageSummary(unittest.TestCase):

    def test_set_plain_language_summary(self):
        digest = '<p>One.</p><p><italic>Two</italic>.</p>'
        expected = (
            b'<root><OtherAbstract Language="eng" Type="plain-language-summary">One. '
            b'<i>Two</i>.</OtherAbstract></root>'
        )
        article = Article()
        article.digest = digest
        parent_tag = Element('root')
        generate.set_plain_language_summary(parent_tag, article)
        self.assertEqual(ElementTree.tostring(parent_tag), expected)


if __name__ == '__main__':
    unittest.main()
