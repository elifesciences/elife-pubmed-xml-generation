from elifearticle import parse
from elifearticle import utils as eautils
from elifetools import utils as etoolsutils
from elifetools import xmlio
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
import datetime
import time
import re
import os
from collections import OrderedDict
from elifepubmed.conf import config, parse_raw_config
from elifepubmed import utils

TMP_DIR = 'tmp'

class PubMedXML(object):
    """
    Generate PubMed XML for the article
    """
    def __init__(self, poa_articles, pubmed_config, pub_date=None, add_comment=True):
        """
        set the root node
        get the article type from the object passed in to the class
        set default values for items that are boilder plate for this XML
        """
        # Set the config
        self.pubmed_config = pubmed_config
        # Create the root XML node
        self.root = Element('ArticleSet')

        # Publication date
        if pub_date is None:
            self.pub_date = time.gmtime()
        else:
            self.pub_date = pub_date

        # Generate batch id
        batch_doi = ''
        if len(poa_articles) == 1:
            # If only one article is supplied, then add the doi to the batch file name
            batch_doi = str(poa_articles[0].manuscript) + '-'
        self.batch_id = (str(self.pubmed_config.get('batch_file_prefix')) + batch_doi +
                                   time.strftime("%Y%m%d%H%M%S", self.pub_date))

        # set comment
        if add_comment:
            self.generated = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_commit = eautils.get_last_commit_to_master()
            self.comment = Comment('generated by ' + str(self.pubmed_config.get('generator')) +
                                   ' at ' + self.generated +
                                   ' from version ' + self.last_commit)
            self.root.append(self.comment)

        self.build(self.root, poa_articles)

    def build(self, root, poa_articles):

        for poa_article in poa_articles:
            # Initialise these as None for each loop
            self.contributors = None
            self.groups = None

            self.article = SubElement(root, "Article")

            self.set_journal(self.article, poa_article)
            self.set_replaces(self.article, poa_article)
            self.set_article_title(self.article, poa_article)
            self.set_e_location_id(self.article, poa_article)
            self.set_language(self.article, poa_article)
            for contrib_type in self.pubmed_config.get('author_contrib_types'):
                self.set_author_list(self.article, poa_article, contrib_type)
            for contrib_type in self.pubmed_config.get('group_author_contrib_types'):
                self.set_group_list(self.article, poa_article, contrib_type)
            self.set_publication_type(self.article, poa_article)
            self.set_article_id_list(self.article, poa_article)
            self.set_history(self.article, poa_article)
            self.set_abstract(self.article, poa_article)
            self.set_copyright_information(self.article, poa_article)
            self.set_coi_statement(self.article, poa_article)
            self.set_object_list(self.article, poa_article)

    def get_pub_type(self, poa_article):
        """
        Given an article object, determine whether the pub_type is for
        PoA article or VoR article
        """
        pub_type = None
        if poa_article.is_poa is True:
            # PoA
            pub_type = "aheadofprint"
        else:
            # VoR
            pub_type = "epublish"
        return pub_type

    def get_pub_date(self, poa_article):
        """
        For using in XML generation, use the article pub date
        or by default use the run time pub date
        """
        pub_date = None

        for date_type in self.pubmed_config.get('pub_date_types'):
            pub_date_obj = poa_article.get_date(date_type)
            if pub_date_obj:
                break

        if pub_date_obj:
            pub_date = pub_date_obj.date
        else:
            # Default use the run time date
            pub_date = self.pub_date
        return pub_date

    def set_journal(self, parent, poa_article):
        self.journal = SubElement(parent, "Journal")

        self.publisher_name = SubElement(self.journal, "PublisherName")
        self.publisher_name.text = poa_article.publisher_name

        self.journal_title = SubElement(self.journal, 'JournalTitle')
        self.journal_title.text = poa_article.journal_title

        self.issn = SubElement(self.journal, 'Issn')
        self.issn.text = poa_article.journal_issn

        pub_date = self.get_pub_date(poa_article)

        self.volume = SubElement(self.journal, "Volume")
        # Use volume from the article unless not present then use the default
        if poa_article.volume:
            self.volume.text = poa_article.volume
        else:
            if pub_date and self.pubmed_config.get("year_of_first_volume"):
                self.volume.text = eautils.calculate_journal_volume(
                    pub_date, self.pubmed_config.get("year_of_first_volume"))

        if poa_article.issue:
            self.issue = SubElement(self.journal, "Issue")
            self.issue.text = poa_article.issue

        # Add the pub date now
        pub_type = self.get_pub_type(poa_article)
        if pub_type:
            self.set_pub_date(self.journal, pub_date, pub_type)

    def set_replaces(self, parent, poa_article):
        """
        Set the Replaces tag, if applicable
        """
        # ways a Replaces tag will be added to the PubMed deposit
        # - is not a poa but was a poa in the past (indicates a version > 1)
        # - article has a version attribute  > 1
        # - article has a replaces attribute set to True
        if ((poa_article.is_poa is False and poa_article.was_ever_poa is True)
            or (poa_article.version and poa_article.version > 1)
            or (hasattr(poa_article, 'replaces') and poa_article.replaces is True)):
            self.replaces = SubElement(parent, 'Replaces')
            self.replaces.set("IdType", "doi")
            self.replaces.text = poa_article.doi

    def set_article_title(self, parent, poa_article):
        """
        Set the titles and title tags allowing sub tags within title
        """
        tag_name = 'ArticleTitle'
        # Pubmed allows <i> tags, not <italic> tags
        tag_converted_title = poa_article.title
        tag_converted_title = eautils.replace_tags(tag_converted_title, 'italic', 'i')
        tag_converted_title = eautils.replace_tags(tag_converted_title, 'bold', 'b')
        tag_converted_title = eautils.replace_tags(tag_converted_title, 'underline', 'u')
        # Specific issue to remove b tag wrapping the entire title, if present
        if tag_converted_title.startswith('<b>') and tag_converted_title.endswith('</b>'):
            tag_converted_title = tag_converted_title.lstrip('<b>')
            tag_converted_title = tag_converted_title.rstrip('</b>')
        tag_converted_title = etoolsutils.escape_unmatched_angle_brackets(
            tag_converted_title, utils.allowed_tags())
        tagged_string = '<' + tag_name + '>' + tag_converted_title + '</' + tag_name + '>'
        reparsed = minidom.parseString(etoolsutils.escape_ampersand(tagged_string).encode('utf-8'))

        root_xml_element = xmlio.append_minidom_xml_to_elementtree_xml(
            parent, reparsed
        )

    def set_e_location_id(self, parent, poa_article):
        self.e_location_id = SubElement(parent, "ELocationID")
        self.e_location_id.set("EIdType", "doi")
        self.e_location_id.text = poa_article.doi

        if poa_article.elocation_id:
            self.e_location_id = SubElement(parent, "ELocationID")
            self.e_location_id.set("EIdType", "pii")
            self.e_location_id.text = poa_article.elocation_id

    def set_language(self, parent, poa_article):
        self.language = SubElement(parent, "Language")
        self.language.text = self.pubmed_config.get('language')

    def set_author_list(self, parent, poa_article, contrib_type=None):
        # If contrib_type is None, all contributors will be added regardless of their type

        if self.contributors is None:
            # Create the XML element on first use
            self.contributors = SubElement(parent, "AuthorList")

        for contributor in poa_article.contributors:
            if contrib_type:
                # Filter by contrib_type if supplied
                if contributor.contrib_type != contrib_type:
                    continue
            # Skip contributors with no surname and no collab
            if  (contributor.surname == "" or contributor.surname is None) \
            and (contributor.collab == "" or contributor.collab is None):
                continue

            self.person_name = SubElement(self.contributors, "Author")

            if contributor.equal_contrib is True:
                self.person_name.set("EqualContrib", "Y")

            if contributor.given_name:
                self.given_name = SubElement(self.person_name, "FirstName")
                self.given_name.text = contributor.given_name
            elif contributor.surname:
                # Empty given_name but has a surname
                self.given_name = SubElement(self.person_name, "FirstName")
                self.given_name.set("EmptyYN", "Y")

            if contributor.surname:
                self.surname = SubElement(self.person_name, "LastName")
                self.surname.text = contributor.surname

            if contributor.collab:
                self.collective_name = SubElement(self.person_name, "CollectiveName")
                self.collective_name.text = contributor.collab

            if contributor.suffix:
                suffix = SubElement(self.person_name, "Suffix")
                suffix.text = contributor.suffix

            # Add each affiliation for multiple affiliation support
            non_blank_aff_count = len([aff for aff in contributor.affiliations if aff.text != ""])
            for aff in contributor.affiliations:
                if aff.text != "":
                    if non_blank_aff_count == 1:
                        self.affiliation = SubElement(self.person_name, "Affiliation")
                        self.affiliation.text = aff.text
                    elif non_blank_aff_count > 1:
                        # Wrap each in AffiliationInfo tag
                        self.affiliation_info = SubElement(self.person_name, "AffiliationInfo")
                        self.affiliation = SubElement(self.affiliation_info, "Affiliation")
                        self.affiliation.text = aff.text

            if contributor.orcid:
                self.orcid = SubElement(self.person_name, "Identifier")
                self.orcid.set("Source", "ORCID")
                self.orcid.text = contributor.orcid

    def set_group_list(self, parent, poa_article, contrib_type=None):
        # If contrib_type is None, all contributors will be added regardless of their type

        if self.groups is None:
            # Create the XML element on first use
            self.groups = SubElement(parent, "GroupList")

        for contributor in poa_article.contributors:
            if contrib_type:
                # Filter by contrib_type if supplied
                if contributor.contrib_type != contrib_type:
                    continue
            # Skip contributors with no surname and no collab
            if  (contributor.surname == "" or contributor.surname is None) \
            and (contributor.collab == "" or contributor.collab is None):
                continue

            # Set the GroupName value
            if contributor.group_author_key:
                # The contributor has a contrib-id contrib-id-type="group-author-key"
                #  Match this value to article contributors of type collab having the same id
                for collab_contrib in poa_article.contributors:
                    if (collab_contrib.collab is not None
                        and collab_contrib.group_author_key == contributor.group_author_key):
                        # Set the individual GroupName to the collab name
                        self.group_name_text = collab_contrib.collab
            elif contributor.collab:
                # If a collab value and no group_author_key then use the collab value
                self.group_name_text = contributor.collab

            # Find existing group with the same name or create it if not exists
            self.group = None
            for group in self.groups.findall('./Group'):
                for group_name in group.findall('./GroupName'):
                    if group_name.text == self.group_name_text:
                        # Matched an existing group tag, use it
                        self.group = group
                        break

            if self.group is None:
                # Create a new group
                self.group = SubElement(self.groups, "Group")

                # Set the GroupName of the group
                self.group_name = SubElement(self.group, "GroupName")
                self.group_name.text = self.group_name_text

            # Add the individual to the group
            individual = SubElement(self.group, "IndividualName")
            if contributor.collab:
                # for on-behalf-of group author values
                self.given_name = SubElement(individual, "FirstName")
                self.given_name.set("EmptyYN", "Y")
                self.surname = SubElement(individual, "LastName")
                self.surname.text = contributor.collab
            else:
                if contributor.given_name:
                    self.given_name = SubElement(individual, "FirstName")
                    self.given_name.text = contributor.given_name
                elif contributor.surname:
                    # Empty given_name but has a surname
                    self.given_name = SubElement(individual, "FirstName")
                    self.given_name.set("EmptyYN", "Y")
                if contributor.surname:
                    self.surname = SubElement(individual, "LastName")
                    self.surname.text = contributor.surname

        # Remove a completely empty GroupList element, if empty
        if len(self.groups) <= 0:
            parent.remove(self.groups)
            self.groups = None

    def set_publication_type(self, parent, poa_article):
        "PubMed will set PublicationType as Journal Article as the default, also the default here"
        types_map = self.pubmed_config.get('publication_types')
        publication_type = utils.pubmed_publication_type(
            poa_article.article_type, poa_article.display_channel, types_map
        )
        if publication_type:
            self.publication_type = SubElement(parent, "PublicationType")
            self.publication_type.text = publication_type

    def set_article_id_list(self, parent, poa_article):
        self.article_id_list = SubElement(parent, "ArticleIdList")
        if poa_article.doi:
            self.article_id = SubElement(self.article_id_list, "ArticleId")
            self.article_id.set("IdType", "doi")
            self.article_id.text = poa_article.doi
        if poa_article.pii:
            self.article_id = SubElement(self.article_id_list, "ArticleId")
            self.article_id.set("IdType", "pii")
            self.article_id.text = poa_article.pii

    def set_pub_date(self, parent, pub_date, pub_type):
        if pub_date:
            self.publication_date = SubElement(parent, "PubDate")
            self.publication_date.set("PubStatus", pub_type)
            year = SubElement(self.publication_date, "Year")
            year.text = str(pub_date.tm_year)
            month = SubElement(self.publication_date, "Month")
            # Get full text name of month
            month.text = time.strftime('%B', pub_date)
            day = SubElement(self.publication_date, "Day")
            day.text = str(pub_date.tm_mday).zfill(2)

    def set_date(self, parent, a_date, date_type):
        if a_date:
            self.date = SubElement(parent, "PubDate")
            self.date.set("PubStatus", date_type)
            year = SubElement(self.date, "Year")
            year.text = str(a_date.tm_year)
            month = SubElement(self.date, "Month")
            month.text = str(a_date.tm_mon).zfill(2)
            day = SubElement(self.date, "Day")
            day.text = str(a_date.tm_mday).zfill(2)

    def set_history(self, parent, poa_article):
        self.history = SubElement(parent, "History")

        for date_type in self.pubmed_config.get('history_date_types'):
            date = poa_article.get_date(date_type)
            if date:
                self.set_date(self.history, date.date, date_type)

        # If the article is VoR and is was ever PoA, then set the aheadofprint history date
        if poa_article.is_poa is False and poa_article.was_ever_poa is True:
            date_type = "aheadofprint"
            date = self.get_pub_date(poa_article)
            if date:
                self.set_date(self.history, date, date_type)

    def set_abstract(self, parent, poa_article):

        tag_name = 'Abstract'
        # Pubmed allows <i> tags, not <italic> tags
        if poa_article.abstract:
            tag_converted_abstract = poa_article.abstract
            tag_converted_abstract = utils.replace_mathml_tags(tag_converted_abstract)
            tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'italic', 'i')
            tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'bold', 'b')
            tag_converted_abstract = eautils.replace_tags(tag_converted_abstract, 'underline', 'u')
            tag_converted_abstract = tag_converted_abstract.replace('<p>', '').replace('</p>', '')
            tag_converted_abstract = etoolsutils.escape_ampersand(tag_converted_abstract)
            not_allowed_tags = ['<sc>', '</sc>']
            for tagname in not_allowed_tags:
                tag_converted_abstract = tag_converted_abstract.replace(tagname, '')
            tag_converted_abstract = etoolsutils.escape_unmatched_angle_brackets(
                tag_converted_abstract, utils.allowed_tags())
            tagged_string = '<' + tag_name + '>' + tag_converted_abstract + '</' + tag_name + '>'
            reparsed = minidom.parseString(tagged_string.encode('utf-8'))

            root_xml_element = xmlio.append_minidom_xml_to_elementtree_xml(
                parent, reparsed
            )
        else:
            # Empty abstract
            self.abstract = SubElement(parent, tag_name)

    def set_copyright_information(self, parent, poa_article):
        if poa_article.license and poa_article.license.copyright_statement:
            copyright_tag = SubElement(parent, "CopyrightInformation")
            copyright_tag.text = poa_article.license.copyright_statement

    def set_coi_statement(self, parent, poa_article):
        "add a CoiStatement as all the conflict values from article contributors"
        coi_list =[]
        coi_map = OrderedDict()

        # step 1 look for contributors with conflicts first
        contributor_list = []
        # look for contributors with conflicts first
        for contributor in poa_article.contributors:
            if (contributor.contrib_type in self.pubmed_config.get('author_contrib_types') and
               contributor.conflict):
                contributor_list.append(contributor)

        # step 2 compile a map of coi statements and their associated contributors
        for contributor in contributor_list:
            for conflict in contributor.conflict:
                # start a list of contributors if the statement is not seen yet
                if conflict not in coi_map:
                    coi_map[conflict] = []
                # add the contributor for processing later
                coi_map[conflict].append(contributor)

        # step 3 concatenate a string for each coi statement with a list of author initials
        for coi, contributors in coi_map.items():
            initials_list = []
            for contributor in contributors:
                initials = utils.contributor_initials(contributor.surname, contributor.given_name)
                if initials != '':
                    initials_list.append(initials)
            all_initials = ', '.join(initials_list)
            # format the final string and add to the list
            coi_list.append(all_initials + ' ' + coi)

        # concatenate the single conflict of interest statement and add the tag
        if coi_list:
            coi_statement_tag = SubElement(parent, "CoiStatement")
            coi_statement_tag.text = utils.join_phrases(coi_list)

    def set_object_list(self, parent, poa_article):
        # Keywords and others go in Object tags
        self.object_list = SubElement(parent, "ObjectList")

        # Add related article data for correction articles
        if poa_article.article_type == "correction":
            for related_article in poa_article.related_articles:
                if related_article.related_article_type == "corrected-article":
                    params = OrderedDict()
                    params["type"] = str(related_article.ext_link_type)
                    params["id"] = str(related_article.xlink_href)
                    object = self.set_object(self.object_list, "Erratum", params)

        # Add research organisms
        for research_organism in poa_article.research_organisms:
            if research_organism.lower() != 'other':
                # Convert the research organism
                research_organism_converted = self.convert_research_organism(research_organism)
                params = {"value": research_organism_converted}
                self.set_object(self.object_list, "keyword", params)

        # Add article categories
        for article_category in poa_article.article_categories:

            if self.pubmed_config.get('split_article_categories') is True:
                if article_category.lower().strip() == 'computational and systems biology':
                    # Edge case category needs special treatment
                    categories = ['Computational biology', 'Systems biology']
                else:
                    # Break on "and" and capitalise the first letter
                    categories = article_category.split('and')
            else:
                categories = [article_category]

            for category in categories:
                category = category.strip().lower()
                params = {"value": category}
                self.set_object(self.object_list, "keyword", params)

        # Add keywords
        for keyword in poa_article.author_keywords:
            params = {"value": keyword}
            self.set_object(self.object_list, "keyword", params)

        # Add grant / funding
        for award in poa_article.funding_awards:
            for award_id in award.award_ids:
                if award.institution_name is not None and award.institution_name != '':
                    params = OrderedDict()
                    params["id"] = award_id
                    params["grantor"] = award.institution_name
                    self.set_object(self.object_list, "grant", params)

        # Finally, do not leave an empty ObjectList tag, if present
        if len(self.object_list) <= 0:
            parent.remove(self.object_list)

    def convert_research_organism(self, research_organism):
        # Lower case except for the first letter followed by a dot by a space
        research_organism_converted = research_organism.lower()
        if re.match('^[a-z]\. ', research_organism_converted):
            # Upper the first character and add to the remainder
            research_organism_converted = (
                research_organism_converted[0].upper() +
                research_organism_converted[1:])
        return research_organism_converted

    def set_object(self, parent, object_type, params):
        # e.g.  <Object Type="keyword"><Param Name="value">human</Param></Object>
        self.object = SubElement(parent, "Object")
        self.object.set("Type", object_type)
        for param_name, param in params.items():
            self.param = SubElement(self.object, "Param")
            self.param.set("Name", param_name)
            self.param.text = param
        return self.object

    def output_XML(self, pretty=False, indent=""):
        encoding = 'utf-8'
        namespaceURI = None
        qualifiedName = "ArticleSet"

        doctype = xmlio.ElifeDocumentType(qualifiedName)
        doctype._identified_mixin_init(
            publicId=self.pubmed_config.get('pubmed_xml_public_id'),
            systemId=self.pubmed_config.get('pubmed_xml_system_id'))

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)
        if doctype:
            reparsed.insertBefore(doctype, reparsed.documentElement)

        if pretty is True:
            return reparsed.toprettyxml(indent, encoding=encoding)
        else:
            return reparsed.toxml(encoding=encoding)


def build_pubmed_xml(poa_articles, config_section="elife", pub_date=None, add_comment=True):
    """
    Given a list of article article objects
    generate PubMed XML from them
    """
    raw_config = config[config_section]
    pubmed_config = parse_raw_config(raw_config)
    return PubMedXML(poa_articles, pubmed_config, pub_date, add_comment)


def pubmed_xml(poa_articles, config_section="elife", pub_date=None, add_comment=True):
    "build PubMed xml and return output as a string"
    pXML = build_pubmed_xml(poa_articles, config_section, pub_date, add_comment)
    return pXML.output_XML()


def pubmed_xml_to_disk(poa_articles, config_section="elife", pub_date=None, add_comment=True):
    "build pubmed xml and write the output to disk"
    pXML = build_pubmed_xml(poa_articles, config_section, pub_date, add_comment)
    xml_string = pXML.output_XML()
    # Write to file
    filename = TMP_DIR + os.sep + pXML.batch_id + '.xml'
    with open(filename, "wb") as fp:
        fp.write(xml_string)


def build_articles_for_pubmed(article_xmls, config_section="elife"):
    "specify some detail and build_parts specific to generating pubmed output"
    raw_config = config[config_section]
    pubmed_config = parse_raw_config(raw_config)
    build_parts = pubmed_config.get('build_parts')
    remove_tags = pubmed_config.get('remove_tags')
    return build_articles(article_xmls, build_parts, remove_tags)


def build_articles(article_xmls, build_parts=None, remove_tags=None):
    return parse.build_articles_from_article_xmls(
        article_xmls, detail="full", build_parts=build_parts, remove_tags=remove_tags)
