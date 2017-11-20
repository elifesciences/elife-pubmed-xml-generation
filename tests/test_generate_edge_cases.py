import unittest
import time
from elifepubmed import generate
from elifearticle.article import Article, Contributor, ArticleDate

class TestGenerateArticleTitle(unittest.TestCase):

    def test_generate_bold_article_title(self):
        "build an article object, set the title, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "<bold>Test article</bold>"
        expected_title = "<ArticleTitle>Test article</ArticleTitle>"
        article = Article(doi, title)
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue(expected_title in pubmed_xml_string)


class TestGenerateArticleType(unittest.TestCase):

    def test_generate_article_type(self):
        "build an article object, set the article_type, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        expected_fragment = "<PublicationType>Editorial</PublicationType>"
        article = Article(doi, title)
        article.article_type = "editorial"
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue(expected_fragment in pubmed_xml_string)


class TestGenerateArticleContributors(unittest.TestCase):

    def test_generate_blank_contributors(self):
        "build an article object, set the contributors, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        contributor1 = Contributor(contrib_type="author", surname=None, given_name=None)
        article.add_contributor(contributor1)
        contributor2 = Contributor(contrib_type="author non-byline", surname=None, given_name=None)
        article.add_contributor(contributor2)
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue('<AuthorList>' not in pubmed_xml_string)
        self.assertTrue('<GroupList>' not in pubmed_xml_string)


    def test_generate_contributor_surname_no_given_name(self):
        "build an article object, set the contributors, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        expected_fragment = '<AuthorList><Author><CollectiveName>Group name</CollectiveName></Author></AuthorList><GroupList><Group><GroupName>Group name</GroupName><IndividualName><FirstName EmptyYN="Y"/><LastName>eLife</LastName></IndividualName></Group></GroupList>'
        article = Article(doi, title)
        contributor1 = Contributor(contrib_type="author", surname=None, given_name=None, collab="Group name")
        contributor1.group_author_key = 'group1'
        article.add_contributor(contributor1)
        contributor2 = Contributor(contrib_type="author non-byline", surname="eLife", given_name=None)
        contributor2.group_author_key = 'group1'
        article.add_contributor(contributor2)
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue(expected_fragment in pubmed_xml_string)


class TestGenerateArticlePOAStatus(unittest.TestCase):

    def test_generate_vor_was_ever_poa(self):
        "build an article object, set the poa status values, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.is_poa = False
        article.was_ever_poa = True
        default_pub_date = time.strptime("2017-07-17 07:17:07", "%Y-%m-%d %H:%M:%S")
        date_instance = ArticleDate('pub', default_pub_date)
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue('<Replaces IdType="doi">' in pubmed_xml_string)
        self.assertTrue('<History><PubDate PubStatus="aheadofprint">' in pubmed_xml_string)


class TestGenerateArticleIssue(unittest.TestCase):

    def test_generate_issue(self):
        """
        until there is a test example that has an article issue in the XML,
        build an article object, set the issue value, generate PubMed XML
        for test coverage
        """
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.issue = "1"
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue('<Issue>1</Issue>' in pubmed_xml_string)


class TestSetCoiStatement(unittest.TestCase):

    def test_set_coi_statement(self):
        """
        test the output of set_coi_statement with generated object data
        """
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # add contributors
        contributor1 = Contributor(contrib_type="author", surname="Ant", given_name="Adam")
        contributor1.conflict = ['No competing interests declared']
        article.add_contributor(contributor1)
        contributor2 = Contributor(contrib_type="author", surname="Bee", given_name="Billie")
        contributor2.conflict = ['Holds the position of Queen Bee']
        article.add_contributor(contributor2)
        contributor3 = Contributor(contrib_type="author", surname="Caterpillar", given_name="Cecil")
        contributor3.conflict = ['No competing interests declared']
        article.add_contributor(contributor3)
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue('<CoiStatement>AA, CC No competing interests declared, BB Holds the position of Queen Bee</CoiStatement>' in pubmed_xml_string)


class TestReplaces(unittest.TestCase):

    def test_set_replaces(self):
        """
        test et_replaces when an article replaces attribute it set
        """
        # first test a version 1 with no replaces tag
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.version = 1
        expected = '<Replaces IdType="doi">10.7554/eLife.00666</Replaces>'
        # generate the PubMed XML
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # expect to not find expected fragment
        self.assertTrue(expected not in pubmed_xml_string)
        # second test setting the replaces value on the article object
        article.replaces = True
        pXML = generate.build_pubmed_xml([article])
        pubmed_xml_string = pXML.output_XML()
        self.assertIsNotNone(pubmed_xml_string)
        # expect to find expected fragment
        self.assertTrue(expected in pubmed_xml_string)


if __name__ == '__main__':
    unittest.main()
