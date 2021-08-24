import unittest
from elifearticle.article import (
    Article,
    Affiliation,
    Contributor,
    FundingAward,
    RelatedArticle,
)
from elifepubmed import generate


class TestGenerateArticleTitle(unittest.TestCase):
    def test_generate_bold_article_title(self):
        "build an article object, set the title, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "<bold>Test article</bold>"
        expected_title = "<ArticleTitle>Test article</ArticleTitle>"
        article = Article(doi, title)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue(expected_title in str(pubmed_xml_string))


class TestGenerateArticleType(unittest.TestCase):
    def test_generate_article_type(self):
        "build an article object, set the article_type, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        expected_fragment = "<PublicationType>Editorial</PublicationType>"
        article = Article(doi, title)
        article.article_type = "editorial"
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue(expected_fragment in str(pubmed_xml_string))

    def test_generate_article_type_correction(self):
        "build an article object, set the article_type and related_articles, generate PubMed XML"
        # create the related article
        related_article = RelatedArticle()
        related_article.xlink_href = "10.7554/eLife.99999"
        related_article.ext_link_type = "doi"
        related_article.related_article_type = "corrected-article"
        # build the main article
        article_type = "correction"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.article_type = article_type
        article.related_articles = [related_article]
        # set some expectations
        expected_fragments = [
            "<PublicationType>Published Erratum</PublicationType>",
            (
                '<Object Type="Erratum"><Param Name="type">doi</Param>'
                + '<Param Name="id">10.7554/eLife.99999</Param>'
            ),
        ]
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        for expected_fragment in expected_fragments:
            self.assertTrue(
                expected_fragment in str(pubmed_xml_string),
                "{fragment} not found".format(fragment=expected_fragment),
            )

    def test_generate_article_type_retraction(self):
        "build an article object, set the article_type and related_articles, generate PubMed XML"
        # create the related article
        related_article = RelatedArticle()
        related_article.xlink_href = "10.7554/eLife.99999"
        related_article.ext_link_type = "doi"
        related_article.related_article_type = "retracted-article"
        # build the main article
        article_type = "retraction"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.article_type = article_type
        article.related_articles = [related_article]
        # set some expectations
        expected_fragments = [
            "<PublicationType>Retraction of Publication</PublicationType>",
            (
                '<Object Type="Retraction"><Param Name="type">doi</Param>'
                + '<Param Name="id">10.7554/eLife.99999</Param>'
            ),
        ]
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        for expected_fragment in expected_fragments:
            self.assertTrue(
                expected_fragment in str(pubmed_xml_string),
                "{fragment} not found".format(fragment=expected_fragment),
            )


class TestGenerateArticleContributors(unittest.TestCase):
    def test_generate_blank_contributors(self):
        "build an article object, set the contributors, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        contributor1 = Contributor(contrib_type="author", surname=None, given_name=None)
        article.add_contributor(contributor1)
        contributor2 = Contributor(
            contrib_type="author non-byline", surname=None, given_name=None
        )
        article.add_contributor(contributor2)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue("<AuthorList>" not in str(pubmed_xml_string))
        self.assertTrue("<GroupList>" not in str(pubmed_xml_string))

    def test_generate_contributor_surname_no_given_name(self):
        "build an article object, set the contributors, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        expected_fragment = (
            "<AuthorList><Author><CollectiveName>Group name</CollectiveName></Author>"
            + "</AuthorList><GroupList><Group><GroupName>Group name</GroupName><IndividualName>"
            + '<FirstName EmptyYN="Y"/><LastName>eLife</LastName></IndividualName></Group>'
            + "</GroupList>"
        )
        article = Article(doi, title)
        contributor1 = Contributor(
            contrib_type="author", surname=None, given_name=None, collab="Group name"
        )
        contributor1.group_author_key = "group1"
        article.add_contributor(contributor1)
        contributor2 = Contributor(
            contrib_type="author non-byline", surname="eLife", given_name=None
        )
        contributor2.group_author_key = "group1"
        article.add_contributor(contributor2)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue(expected_fragment in str(pubmed_xml_string))


class TestGenerateArticlePOAStatus(unittest.TestCase):
    def test_generate_vor_was_ever_poa(self):
        "build an article object, set the poa status values, generate PubMed XML"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        article.is_poa = False
        article.was_ever_poa = True
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue('<Replaces IdType="doi">' in str(pubmed_xml_string))
        self.assertTrue(
            '<History><PubDate PubStatus="aheadofprint">' in str(pubmed_xml_string)
        )


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
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        self.assertTrue("<Issue>1</Issue>" in str(pubmed_xml_string))


class TestSetCoiStatement(unittest.TestCase):
    def test_set_coi_statement(self):
        """
        test the output of set_coi_statement with generated object data
        """
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # add contributors
        contributor1 = Contributor(
            contrib_type="author", surname="Ant", given_name="Adam"
        )
        contributor1.conflict = ["No competing interests declared"]
        article.add_contributor(contributor1)
        contributor2 = Contributor(
            contrib_type="author", surname="Bee", given_name="Billie"
        )
        contributor2.conflict = ["Holds the position of <italic>Queen Bee</italic>"]
        article.add_contributor(contributor2)
        contributor3 = Contributor(
            contrib_type="author", surname="Caterpillar", given_name="Cecil"
        )
        contributor3.conflict = ["No competing interests declared"]
        article.add_contributor(contributor3)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look for the expected string in the output
        expected_fragment = (
            "<CoiStatement>AA, CC No competing interests declared, "
            + "BB Holds the position of Queen Bee</CoiStatement>"
        )
        self.assertTrue(expected_fragment in str(pubmed_xml_string))


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
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # expect to not find expected fragment
        self.assertTrue(expected not in str(pubmed_xml_string))
        # second test setting the replaces value on the article object
        article.replaces = True
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # expect to find expected fragment
        self.assertTrue(expected in str(pubmed_xml_string))


class TestGenerateArticleFunding(unittest.TestCase):
    def test_generate_funding(self):
        """
        Test incomplete funding data for test coverage
        """
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # add some blank funding with no institution_name
        funding = FundingAward()
        article.add_funding_award(funding)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # A quick test just look in a string of the output
        self.assertTrue("<grant>" not in str(pubmed_xml_string))


class TestSetGroupList(unittest.TestCase):
    def test_set_group_list_no_individuals(self):
        "test a collab contributor with no group member contributors"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # add contributors
        group_author_name = "Test Group"
        contributor1 = Contributor(
            contrib_type="author",
            surname=None,
            given_name=None,
            collab=group_author_name,
        )
        contributor1.group_author_key = group_author_name
        article.add_contributor(contributor1)
        # add another group with no individuals
        group_author_name = "Test Group Two"
        contributor2 = Contributor(
            contrib_type="author",
            surname=None,
            given_name=None,
            collab=group_author_name,
        )
        contributor2.group_author_key = group_author_name
        article.add_contributor(contributor2)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # assertions
        self.assertTrue(
            "<CollectiveName>Test Group</CollectiveName>" in str(pubmed_xml_string)
        )
        self.assertTrue("<GroupList>" not in str(pubmed_xml_string))

    def test_set_group_list_with_individual(self):
        "test one collab contributor with one group member contributor"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # add contributors
        group_author_name = "Test Group"
        contributor1 = Contributor(
            contrib_type="author",
            surname=None,
            given_name=None,
            collab=group_author_name,
        )
        contributor1.group_author_key = group_author_name
        article.add_contributor(contributor1)
        contributor2 = Contributor(
            contrib_type="author", surname="Ant", given_name="Adam"
        )
        contributor2.group_author_key = group_author_name
        aff = Affiliation()
        aff.text = "Anthill Institute"
        contributor2.set_affiliation(aff)
        article.add_contributor(contributor2)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # assertions
        self.assertTrue(
            "<CollectiveName>Test Group</CollectiveName>" in str(pubmed_xml_string)
        )
        self.assertTrue(
            "<GroupList>"
            "<Group><GroupName>Test Group</GroupName>"
            "<IndividualName>"
            "<FirstName>Adam</FirstName>"
            "<LastName>Ant</LastName>"
            "<Affiliation>Anthill Institute</Affiliation>"
            "</IndividualName></Group>"
            "</GroupList>" in str(pubmed_xml_string)
        )

    def test_set_group_list_complex(self):
        "test two types of collab, one with individual and one without"
        doi = "10.7554/eLife.00666"
        title = "Test article"
        article = Article(doi, title)
        # add contributors
        group_author_name_1 = "Group with Individual"
        contributor1 = Contributor(
            contrib_type="author",
            surname=None,
            given_name=None,
            collab=group_author_name_1,
        )
        contributor1.group_author_key = group_author_name_1
        article.add_contributor(contributor1)

        contributor2 = Contributor(
            contrib_type="author", surname="Ant", given_name="Adam"
        )
        contributor2.group_author_key = group_author_name_1
        article.add_contributor(contributor2)

        group_author_name_2 = "Group without Individual"
        contributor3 = Contributor(
            contrib_type="author",
            surname=None,
            given_name=None,
            collab=group_author_name_2,
        )
        contributor3.group_author_key = group_author_name_2
        article.add_contributor(contributor3)
        # generate the PubMed XML
        p_xml = generate.build_pubmed_xml([article])
        pubmed_xml_string = p_xml.output_xml()
        self.assertIsNotNone(pubmed_xml_string)
        # assertions
        self.assertTrue(
            "<CollectiveName>Group with Individual</CollectiveName>"
            in str(pubmed_xml_string)
        )
        self.assertTrue(
            "<CollectiveName>Group without Individual</CollectiveName>"
            in str(pubmed_xml_string)
        )
        self.assertTrue(
            "<GroupList>"
            "<Group><GroupName>Group with Individual</GroupName>"
            "<IndividualName>"
            "<FirstName>Adam</FirstName>"
            "<LastName>Ant</LastName>"
            "</IndividualName></Group>"
            "</GroupList>" in str(pubmed_xml_string)
        )


if __name__ == "__main__":
    unittest.main()
