import unittest
from elifepubmed import generate
from elifearticle.article import Article, Contributor

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
        expected_fragment = "<PublicationType>EDITORIAL</PublicationType>"
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

if __name__ == '__main__':
    unittest.main()
