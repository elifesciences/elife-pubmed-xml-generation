import unittest
import time
import os
from xml.etree.ElementTree import Element
from xml.etree import ElementTree
from elifearticle.article import Article, Citation, ClinicalTrial, Dataset
from elifepubmed import generate
from elifepubmed.conf import config, parse_raw_config


TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
generate.TMP_DIR = TEST_BASE_PATH + "tmp" + os.sep


def read_file_content(file_name):
    with open(file_name, "rb") as open_file:
        return open_file.read()


class TestGenerate(unittest.TestCase):
    def setUp(self):
        self.passes = []
        self.default_pub_date = time.strptime(
            "2017-07-17 07:17:07", "%Y-%m-%d %H:%M:%S"
        )
        self.passes.append(
            (
                "elife-15743-v1.xml",
                "elife-pubmed-15743-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "elife_poa_e12717.xml",
                "elife-pubmed-12717-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "elife_poa_e00003.xml",
                "elife-pubmed-00003-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "elife-02935-v2.xml",
                "elife-pubmed-02935-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "elife-00666.xml",
                "elife-pubmed-00666-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "bmjopen-4-e003269.xml",
                "pubmed-bmjopen-2013-003269-20170717071707.xml",
                "bmjopen",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "pb369-jats.xml",
                "pb-pubmed-369-20170717071707.xml",
                "pb",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "elife-60675-v2.xml",
                "elife-pubmed-60675-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )
        self.passes.append(
            (
                "elife-66683.xml",
                "elife-pubmed-66683-20170717071707.xml",
                "elife",
                self.default_pub_date,
            )
        )

    def test_parse(self):
        for (
            article_xml_file,
            pubmed_xml_file,
            config_section,
            pub_date,
        ) in self.passes:
            file_path = TEST_DATA_PATH + article_xml_file
            articles = generate.build_articles_for_pubmed(
                article_xmls=[file_path], config_section=config_section
            )
            p_xml = generate.build_pubmed_xml(articles, config_section, pub_date, False)
            pubmed_xml = str(p_xml.output_xml(pretty=True))
            model_pubmed_xml = str(read_file_content(TEST_DATA_PATH + pubmed_xml_file))
            self.assertEqual(pubmed_xml, model_pubmed_xml)
            # check the batch_id will be similar to the XML filename
            self.assertEqual(p_xml.batch_id + ".xml", pubmed_xml_file)

    def test_pubmed_xml(self):
        "test at least one article through this function for test coverage"
        article_xml_file = "elife-15743-v1.xml"
        config_section = "elife"
        pub_date = self.default_pub_date
        file_path = TEST_DATA_PATH + article_xml_file
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section
        )
        pubmed_xml = generate.pubmed_xml(articles, config_section, pub_date, False)
        self.assertIsNotNone(pubmed_xml)

    def test_parse_do_no_pass_pub_date(self):
        """
        For test coverage build a PubMedXML object without passing in a pub_date
        and also test pretty output too for coverage
        """
        article_xml_file = "elife-15743-v1.xml"
        file_path = TEST_DATA_PATH + article_xml_file
        config_section = "elife"
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section
        )
        raw_config = config[config_section]
        pubmed_config = parse_raw_config(raw_config)
        pubmed_object = generate.PubMedXML(articles, pubmed_config, None, True)
        self.assertIsNotNone(pubmed_object.pub_date)
        self.assertIsNotNone(pubmed_object.generated)
        self.assertIsNotNone(pubmed_object.last_commit)
        self.assertIsNotNone(pubmed_object.comment)
        self.assertIsNotNone(pubmed_object.output_xml(pretty=True, indent="\t"))

    def test_pubmed_xml_to_disk(self):
        "test writing to disk for test coverage"
        article_xml_file = "elife_poa_e00003.xml"
        pubmed_xml_file = "elife-pubmed-00003-20170717071707.xml"
        config_section = "elife"
        pub_date = self.default_pub_date
        file_path = TEST_DATA_PATH + article_xml_file
        # build the article object
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section
        )
        # generate and write to disk
        generate.pubmed_xml_to_disk(articles, config_section, pub_date, False, True)
        # check the output matches
        with open(TEST_DATA_PATH + pubmed_xml_file, "rb") as file_p:
            expected_output = file_p.read()
        with open(generate.TMP_DIR + pubmed_xml_file, "rb") as file_p:
            generated_output = file_p.read()
        self.assertEqual(generated_output, expected_output)

    def test_set_is_poa(self):
        "test a method to make a non-eLife article aheadofprint by setting is_poa"
        article_xml_file = "pb369-jats.xml"
        file_path = TEST_DATA_PATH + article_xml_file
        config_section = "pb"
        articles = generate.build_articles_for_pubmed(
            article_xmls=[file_path], config_section=config_section
        )
        # set the is_poa value
        articles[0].is_poa = True
        pubmed_xml = str(generate.pubmed_xml(articles, config_section))
        self.assertTrue(
            '<PubDate PubStatus="aheadofprint">' in pubmed_xml,
            "aheadofprint date not found in PubMed XML after setting is_poa",
        )


class TestDataset(unittest.TestCase):
    def test_dataset_details_empty(self):
        """test an empty Dataset object"""
        dataset = Dataset()
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertIsNone(assigning_authority)
        self.assertIsNone(id_value)

    def test_dataset_details_doi(self):
        """test Dataset that has a doi"""
        doi = "doi"
        dataset = Dataset()
        dataset.doi = doi
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertIsNone(assigning_authority)
        self.assertEqual(id_value, doi)

    def test_dataset_details_accession_id(self):
        """test Dataset that has a accession_id"""
        accession_id = "accession_id"
        dataset = Dataset()
        dataset.accession_id = accession_id
        assigning_authority, id_value = generate.dataset_details(dataset)
        self.assertIsNone(assigning_authority)
        self.assertEqual(id_value, accession_id)

    def test_dataset_details_both(self):
        """test Dataset that has both a doi and accession_id"""
        uri = "www.ncbi.nlm.nih.gov/geo"
        doi = "doi"
        accession_id = "accession_id"
        expected_authority_value = "NCBI:geo"
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
        uri = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE48760"
        expected = "NCBI:geo"
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)

    def test_dataset_assigning_authority_ncbi_dbgap(self):
        """NCBI dbgap"""
        uri = "https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs001660.v1.p1"
        expected = "NCBI:dbgap"
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)

    def test_dataset_assigning_authority_ncbi_nucleotide(self):
        """NCBI nucleotide"""
        uri = "https://www.ncbi.nlm.nih.gov/nuccore/KY616976"
        expected = "NCBI:nucleotide"
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)

    def test_dataset_assigning_authority_ncbi_sra(self):
        """NCBI sra"""
        uri = "https://www.ncbi.nlm.nih.gov/sra/?term=SRA012474"
        expected = "NCBI:sra"
        assigning_authority = generate.dataset_assigning_authority(uri)
        self.assertEqual(assigning_authority, expected)


class TestCleanAbstract(unittest.TestCase):
    def test_clean_abstract(self):
        abstract = (
            "<abstract>"
            '<object-id pub-id-type="doi">10.7554/eLife.00666.001</object-id>'
            '<sec id="abs1">'
            "<title>Background:</title>"
            '<p>Lorem ipsum <xref ref-type="bibr" rid="bib12">Anon (2002)</xref> '
            '<ext-link ext-link-type="uri" xlink:href="https://elifesciences.org/">'
            "eLife</ext-link> "
            '<related-object xlink:href="https://clinicaltrials.gov/show/NCT02836002">'
            "NCT02836002</related-object></p>"
            "</sec>"
            "</abstract>"
        )
        expected = (
            '<sec id="abs1">'
            "<title>Background:</title>"
            "<p>Lorem ipsum Anon (2002) eLife NCT02836002</p>"
            "</sec>"
        )
        self.assertEqual(generate.clean_abstract(abstract), expected)


class TestPlainLanguageSummary(unittest.TestCase):
    def test_set_plain_language_summary(self):
        digest = "<p>One.</p><p><italic>Two</italic>.</p>"
        expected = (
            b'<root><OtherAbstract Language="eng" Type="plain-language-summary">One. '
            b"<i>Two</i>.</OtherAbstract></root>"
        )
        article = Article()
        article.digest = digest
        parent_tag = Element("root")
        generate.set_plain_language_summary(parent_tag, article)
        self.assertEqual(ElementTree.tostring(parent_tag), expected)

    def test_set_plain_language_summary_edge_case(self):
        "test escaping ampersand character"
        digest = "<p>CUT&Tag.</p>"
        expected = (
            b'<root><OtherAbstract Language="eng" Type="plain-language-summary">'
            b"CUT&amp;Tag.</OtherAbstract></root>"
        )
        article = Article()
        article.digest = digest
        parent_tag = Element("root")
        generate.set_plain_language_summary(parent_tag, article)
        self.assertEqual(ElementTree.tostring(parent_tag), expected)


class TestSetDatasets(unittest.TestCase):
    def test_set_datasets(self):
        """edge case testing of ignoring duplciate records and case-insensitive name matching"""
        parent_tag = Element("root")
        expected = (
            b"<root>"
            b'<Object Type="Dryad"><Param Name="id">10.5061/dryad.example</Param></Object>'
            b'<Object Type="NCBI:geo"><Param Name="id">GSE48760</Param></Object>'
            b'<Object Type="figshare"><Param Name="id">example</Param></Object>'
            b"</root>"
        )
        article = Article()
        dataset = Dataset()
        dataset.uri = "10.5061/dryad.example"
        dataset.doi = "10.5061/dryad.example"
        article.datasets.append(dataset)
        # first ref is a duplicate should be ignored
        citation1 = Citation()
        citation1.publication_type = "data"
        citation1.source = "Dryad Digital Repository"
        citation1.doi = "10.5061/dryad.example"
        article.ref_list.append(citation1)
        # second ref, should be added
        citation2 = Citation()
        citation2.publication_type = "data"
        citation2.source = "NCBI Gene Expression Omnibus"
        citation2.accession = "GSE48760"
        article.ref_list.append(citation2)
        # third ref is a duplicate with different case sensitivity, should be ignored
        citation3 = Citation()
        citation3.publication_type = "data"
        citation1.source = "dryad digital repository"
        citation1.doi = "10.5061/dryad.example"
        article.ref_list.append(citation3)
        # fourth ref tests case insensitive matching, should be added
        citation4 = Citation()
        citation4.publication_type = "data"
        citation4.source = "figShare"
        citation4.accession = "example"
        article.ref_list.append(citation4)

        generate.set_datasets(parent_tag, article)
        self.assertEqual(ElementTree.tostring(parent_tag), expected)


class TestSetClinicalTrials(unittest.TestCase):
    def test_set_clinical_trials(self):
        parent_tag = Element("root")
        expected = (
            b"<root>"
            b'<Object Type="ClinicalTrials.gov"><Param Name="id">TEST999</Param></Object>'
            b"</root>"
        )
        article = Article()
        clinical_trial = ClinicalTrial()
        clinical_trial.source_id = "ClinicalTrials.gov"
        clinical_trial.source_id_type = "registry-name"
        clinical_trial.document_id = "TEST999"
        clinical_trial.content_type = "preResults"
        article.clinical_trials = [clinical_trial]

        generate.set_clinical_trials(parent_tag, article)
        self.assertEqual(ElementTree.tostring(parent_tag), expected)


if __name__ == "__main__":
    unittest.main()
