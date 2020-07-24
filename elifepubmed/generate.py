import time
import re
import os
from collections import OrderedDict
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
from elifearticle import parse
from elifearticle import utils as eautils
from elifetools import utils as etoolsutils
from elifetools import xmlio
from elifepubmed.conf import config, parse_raw_config
from elifepubmed import utils

TMP_DIR = 'tmp'


ASSIGNING_AUTHORITY_URI_MAP = {
    '10.5061/dryad': 'Dryad',
    'www.ncbi.nlm.nih.gov/geo': 'NCBI:geo',
    'www.ncbi.nlm.nih.gov/projects/gap': 'NCBI:dbgap',
    'www.ncbi.nlm.nih.gov/nuccore': 'NCBI:nucleotide',
    'www.ncbi.nlm.nih.gov/sra': 'NCBI:sra'
    }


# map of XML citation source value to PubMed dataset assigning authority value
DATA_REF_SOURCE_MAP = {
    'Dryad Digital Repository': 'Dryad',
    'figshare': 'figshare',
    'NCBI Assembly': 'NCBI:genome',
    'NCBI BioProject': 'BioProject',
    'NCBI dbGaP': 'NCBI:dbgap',
    'NCBI GenBank': 'NCBI:genbank',
    'NCBI Gene Expression Omnibus': 'NCBI:geo',
    'NCBI Nucleotide': 'NCBI:nucleotide',
    'NCBI PopSet': 'NCBI:popset',
    'NCBI Protein': 'NCBI:protein',
    'NCBI Sequence Read Archive': 'NCBI:sra',
    'RCSB Protein Data Bank': 'PDB',
    'Worldwide Protein Data Bank': 'PDB'
}


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

        self.contributors = None
        self.groups = None

        self.build(self.root, poa_articles)

    def build(self, root, poa_articles):

        for poa_article in poa_articles:
            # Initialise these as None for each loop
            self.contributors = None
            self.groups = None

            article_tag = SubElement(root, "Article")

            self.set_journal(article_tag, poa_article)
            set_replaces(article_tag, poa_article)
            set_article_title(article_tag, poa_article)
            set_e_location_id(article_tag, poa_article)
            set_language(article_tag, self.pubmed_config.get('language'))
            for contrib_type in self.pubmed_config.get('author_contrib_types'):
                self.set_author_list(article_tag, poa_article, contrib_type)
            for contrib_type in self.pubmed_config.get('group_author_contrib_types'):
                self.set_group_list(article_tag, poa_article, contrib_type)
            set_publication_type(article_tag, poa_article,
                                 self.pubmed_config.get('publication_types'))
            set_article_id_list(article_tag, poa_article)
            self.set_history(article_tag, poa_article)
            set_abstract(article_tag, poa_article,
                         self.pubmed_config.get('abstract_label_types'))
            set_plain_language_summary(article_tag, poa_article)
            set_copyright_information(article_tag, poa_article)
            set_coi_statement(article_tag, poa_article,
                              self.pubmed_config.get('author_contrib_types'))
            set_object_list(article_tag, poa_article,
                            self.pubmed_config.get('split_article_categories'))

    def set_journal(self, parent, poa_article):
        journal_tag = SubElement(parent, "Journal")

        publisher_name = SubElement(journal_tag, "PublisherName")
        publisher_name.text = poa_article.publisher_name

        journal_title = SubElement(journal_tag, 'JournalTitle')
        journal_title.text = poa_article.journal_title

        issn = SubElement(journal_tag, 'Issn')
        issn.text = poa_article.journal_issn

        pub_date = get_pub_date(poa_article, self.pubmed_config.get('pub_date_types'),
                                self.pub_date)

        volume = SubElement(journal_tag, "Volume")
        # Use volume from the article unless not present then use the default
        if poa_article.volume:
            volume.text = poa_article.volume
        else:
            if pub_date and self.pubmed_config.get("year_of_first_volume"):
                volume.text = eautils.calculate_journal_volume(
                    pub_date, self.pubmed_config.get("year_of_first_volume"))

        if poa_article.issue:
            issue = SubElement(journal_tag, "Issue")
            issue.text = poa_article.issue

        # Add the pub date now
        pub_type = get_pub_type(poa_article)
        if pub_type:
            set_pub_date(journal_tag, pub_date, pub_type)

    def set_author_list(self, parent, poa_article, contrib_type=None):
        # If contrib_type is None, all contributors will be added regardless of their type

        if self.contributors is None:
            # Create the XML element on first use
            self.contributors = SubElement(parent, "AuthorList")

        for contributor in poa_article.contributors:
            set_contributor(self.contributors, contributor, contrib_type)

    def set_group_list(self, parent, poa_article, contrib_type=None):
        # If contrib_type is None, all contributors will be added regardless of their type

        if self.groups is None:
            # Create the XML element on first use
            self.groups = SubElement(parent, "GroupList")

        for contributor in poa_article.contributors:
            if contrib_type and contributor.contrib_type != contrib_type:
                # Filter by contrib_type if supplied
                continue
            # Skip contributors with no surname and no collab
            if not contributor.surname and not contributor.collab:
                continue

            group_name_text = get_group_name_text(poa_article, contributor)

            # Find existing group with the same name or create it if not exists
            matched_group = group_exists(self.groups, group_name_text)
            if matched_group is None:
                # Create a new group
                group_tag = SubElement(self.groups, "Group")
                # Set the GroupName of the group
                group_name = SubElement(group_tag, "GroupName")
                group_name.text = group_name_text

            # Add the individual to the group
            set_group_individual(group_tag, contributor)

        # Remove a completely empty GroupList element, if empty
        if len(self.groups) <= 0:
            parent.remove(self.groups)
            self.groups = None

    def set_history(self, parent, poa_article):
        history = SubElement(parent, "History")

        for date_type in self.pubmed_config.get('history_date_types'):
            date = poa_article.get_date(date_type)
            if date:
                set_date(history, date.date, date_type)

        # If the article is VoR and is was ever PoA, then set the aheadofprint history date
        if poa_article.is_poa is False and poa_article.was_ever_poa is True:
            date_type = "aheadofprint"
            date = get_pub_date(poa_article, self.pubmed_config.get('pub_date_types'),
                                self.pub_date)
            if date:
                set_date(history, date, date_type)

    def output_xml(self, pretty=False, indent=""):
        encoding = 'utf-8'
        qualified_name = "ArticleSet"

        doctype = xmlio.ElifeDocumentType(qualified_name)
        doctype._identified_mixin_init(
            publicId=self.pubmed_config.get('pubmed_xml_public_id'),
            systemId=self.pubmed_config.get('pubmed_xml_system_id'))

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)
        if doctype:
            reparsed.insertBefore(doctype, reparsed.documentElement)

        if pretty is True:
            return reparsed.toprettyxml(indent, encoding=encoding)
        return reparsed.toxml(encoding=encoding)


def set_group_individual(parent, contributor):
    # Add the individual to the group
    individual = SubElement(parent, "IndividualName")
    if contributor.collab:
        # for on-behalf-of group author values
        given_name = SubElement(individual, "FirstName")
        given_name.set("EmptyYN", "Y")
        surname = SubElement(individual, "LastName")
        surname.text = contributor.collab
    else:
        set_first_name(individual, contributor)
        set_surname(individual, contributor)


def group_exists(group_tags, group_name_text):
    "look in the Group tags if the group exists already"
    matched_group = None
    for group in group_tags.findall('./Group'):
        for group_name in group.findall('./GroupName'):
            if group_name.text == group_name_text:
                # Matched an existing group tag, use it
                matched_group = group
                break
    return matched_group


def get_group_name_text(poa_article, contributor):
    "for setting groups find the group name text in the contributors"
    # Set the GroupName value
    group_name_text = None
    if contributor.group_author_key:
        # The contributor has a contrib-id contrib-id-type="group-author-key"
        #  Match this value to article contributors of type collab having the same id
        for collab_contrib in poa_article.contributors:
            if (collab_contrib.collab is not None
                    and collab_contrib.group_author_key == contributor.group_author_key):
                # Set the individual GroupName to the collab name
                group_name_text = collab_contrib.collab
    elif contributor.collab:
        # If a collab value and no group_author_key then use the collab value
        group_name_text = contributor.collab
    return group_name_text


def set_first_name(parent, contributor):
    if contributor.given_name:
        given_name = SubElement(parent, "FirstName")
        given_name.text = contributor.given_name
    elif contributor.surname:
        # Empty given_name but has a surname
        given_name = SubElement(parent, "FirstName")
        given_name.set("EmptyYN", "Y")


def set_surname(parent, contributor):
    if contributor.surname:
        surname = SubElement(parent, "LastName")
        surname.text = contributor.surname


def set_contributor(parent, contributor, contrib_type):
    "set contributor tag details"
    # Filter by contrib_type if supplied
    if contrib_type and contributor.contrib_type != contrib_type:
        # Filter by contrib_type if supplied
        return
    # Skip contributors with no surname and no collab
    if not contributor.surname and not contributor.collab:
        return

    person_name = SubElement(parent, "Author")

    if contributor.equal_contrib is True:
        person_name.set("EqualContrib", "Y")

    set_first_name(person_name, contributor)
    set_surname(person_name, contributor)

    if contributor.collab:
        collective_name = SubElement(person_name, "CollectiveName")
        collective_name.text = contributor.collab

    if contributor.suffix:
        suffix = SubElement(person_name, "Suffix")
        suffix.text = contributor.suffix

    # Add each affiliation for multiple affiliation support
    non_blank_aff_count = len([aff for aff in contributor.affiliations if aff.text != ""])
    for aff in contributor.affiliations:
        if aff.text != "":
            if non_blank_aff_count == 1:
                affiliation = SubElement(person_name, "Affiliation")
                affiliation.text = aff.text
            elif non_blank_aff_count > 1:
                # Wrap each in AffiliationInfo tag
                affiliation_info = SubElement(person_name, "AffiliationInfo")
                affiliation = SubElement(affiliation_info, "Affiliation")
                affiliation.text = aff.text

    if contributor.orcid:
        orcid = SubElement(person_name, "Identifier")
        orcid.set("Source", "ORCID")
        orcid.text = contributor.orcid


def set_publication_type(parent, poa_article, types_map):
    "PubMed will set PublicationType as Journal Article as the default, also the default here"
    publication_type = utils.pubmed_publication_type(
        poa_article.article_type, poa_article.display_channel, types_map
    )
    if publication_type:
        publication_type_tag = SubElement(parent, "PublicationType")
        publication_type_tag.text = publication_type


def get_pub_date(poa_article, pub_date_types, default_pub_date):
    """
    For using in XML generation, use the article pub date
    or by default use the run time pub date
    """
    pub_date = None

    for date_type in pub_date_types:
        pub_date_obj = poa_article.get_date(date_type)
        if pub_date_obj:
            break

    if pub_date_obj:
        pub_date = pub_date_obj.date
    else:
        # Default use the run time date
        pub_date = default_pub_date
    return pub_date


def set_language(parent, language):
    language_tag = SubElement(parent, "Language")
    language_tag.text = language


def set_abstract(parent, poa_article, abstract_label_types):
    "set the Abstract"
    abstract_tag = SubElement(parent, 'Abstract')
    if poa_article.abstract:
        sections = utils.abstract_parts(poa_article.abstract, abstract_label_types)
        for section in sections:
            if section.get('text'):
                set_abstract_text(abstract_tag, section.get('text'),
                                  section.get('label'))
    else:
        # Add an empty abstract
        set_abstract_text(abstract_tag, '', '')


def set_plain_language_summary(parent, article):
    "set an OtherAbstract tag to include the digest as plain-language-summary"
    tag_name = 'OtherAbstract'
    attr_map = {
        'Language': 'eng',
        'Type': 'plain-language-summary'
    }
    if hasattr(article, 'digest') and article.digest:
        tag_converted_digest = utils.replace_inline_tags(article.digest)
        # tweak to add spaces between paragraph tags
        tag_converted_digest = tag_converted_digest.replace('</p><p>', '</p> <p>')
        tag_converted_digest = eautils.remove_tag('p', tag_converted_digest)
        tag_converted_digest = etoolsutils.escape_unmatched_angle_brackets(
            tag_converted_digest, utils.allowed_tags())
        minidom_tag = xmlio.reparsed_tag(
            tag_name, tag_converted_digest, attributes_text=eautils.attr_string(attr_map))
        xmlio.append_minidom_xml_to_elementtree_xml(
            parent, minidom_tag, attributes=attr_map
        )


def set_coi_statement(parent, poa_article, author_contrib_types):
    "add a CoiStatement as all the conflict values from article contributors"
    coi_list = []
    coi_map = OrderedDict()

    # step 1 look for contributors with conflicts first
    contributor_list = []
    # look for contributors with conflicts first
    for contributor in poa_article.contributors:
        if (contributor.contrib_type in author_contrib_types and
                contributor.conflict):
            contributor_list.append(contributor)

    # step 2 compile a map of coi statements and their associated contributors
    for contributor in contributor_list:
        for conflict in contributor.conflict:
            # remove inline tags
            if '<' in conflict:
                for tag_name in utils.allowed_tag_names():
                    conflict = eautils.remove_tag(tag_name, conflict)
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


def set_replaces(parent, poa_article):
    """
    Set the Replaces tag, if applicable
    """
    # ways a Replaces tag will be added to the PubMed deposit
    # - is not a poa but was a poa in the past (indicates a version > 1)
    # - article has a version attribute  > 1
    # - article has a replaces attribute set to True
    add_replaces_tag = False
    if poa_article.is_poa is False and poa_article.was_ever_poa is True:
        add_replaces_tag = True
    if poa_article.version and poa_article.version > 1:
        add_replaces_tag = True
    if hasattr(poa_article, 'replaces') and poa_article.replaces is True:
        add_replaces_tag = True
    if add_replaces_tag:
        replaces = SubElement(parent, 'Replaces')
        replaces.set("IdType", "doi")
        replaces.text = poa_article.doi


def set_article_title(parent, poa_article):
    """
    Set the titles and title tags allowing sub tags within title
    """
    tag_name = 'ArticleTitle'

    tag_converted_title = utils.replace_inline_tags(poa_article.title)
    # Specific issue to remove b tag wrapping the entire title, if present
    if tag_converted_title.startswith('<b>') and tag_converted_title.endswith('</b>'):
        tag_converted_title = tag_converted_title.lstrip('<b>')
        tag_converted_title = tag_converted_title.rstrip('</b>')
    tag_converted_title = etoolsutils.escape_unmatched_angle_brackets(
        tag_converted_title, utils.allowed_tags())
    tag_converted_title = etoolsutils.escape_ampersand(tag_converted_title)
    minidom_tag = xmlio.reparsed_tag(tag_name, tag_converted_title)
    xmlio.append_minidom_xml_to_elementtree_xml(
        parent, minidom_tag
    )


def set_e_location_id(parent, poa_article):
    e_location_id = SubElement(parent, "ELocationID")
    e_location_id.set("EIdType", "doi")
    e_location_id.text = poa_article.doi

    if poa_article.elocation_id:
        e_location_id = SubElement(parent, "ELocationID")
        e_location_id.set("EIdType", "pii")
        e_location_id.text = poa_article.elocation_id


def set_article_id_list(parent, poa_article):
    article_id_list = SubElement(parent, "ArticleIdList")
    if poa_article.doi:
        article_id = SubElement(article_id_list, "ArticleId")
        article_id.set("IdType", "doi")
        article_id.text = poa_article.doi
    if poa_article.pii:
        article_id = SubElement(article_id_list, "ArticleId")
        article_id.set("IdType", "pii")
        article_id.text = poa_article.pii


def set_pub_date(parent, pub_date, pub_type):
    if pub_date:
        publication_date = SubElement(parent, "PubDate")
        publication_date.set("PubStatus", pub_type)
        year = SubElement(publication_date, "Year")
        year.text = str(pub_date.tm_year)
        month = SubElement(publication_date, "Month")
        # Get full text name of month
        month.text = time.strftime('%B', pub_date)
        day = SubElement(publication_date, "Day")
        day.text = str(pub_date.tm_mday).zfill(2)


def set_date(parent, a_date, date_type):
    if a_date:
        date = SubElement(parent, "PubDate")
        date.set("PubStatus", date_type)
        year = SubElement(date, "Year")
        year.text = str(a_date.tm_year)
        month = SubElement(date, "Month")
        month.text = str(a_date.tm_mon).zfill(2)
        day = SubElement(date, "Day")
        day.text = str(a_date.tm_mday).zfill(2)


def set_abstract_text(parent, abstract, label=""):
    "set the AbstractText value of an Abstract given an abstract string"
    tag_name = 'AbstractText'
    attr_map = {
        'Label': label
    }
    tag_converted_abstract = abstract
    tag_converted_abstract = utils.replace_mathml_tags(tag_converted_abstract)
    tag_converted_abstract = utils.replace_inline_tags(tag_converted_abstract)
    tag_converted_abstract = eautils.remove_tag('p', tag_converted_abstract)
    tag_converted_abstract = etoolsutils.escape_ampersand(tag_converted_abstract)
    not_allowed_tags = ['sc']
    for tagname in not_allowed_tags:
        tag_converted_abstract = eautils.remove_tag(tagname, tag_converted_abstract)
    tag_converted_abstract = etoolsutils.escape_unmatched_angle_brackets(
        tag_converted_abstract, utils.allowed_tags())
    minidom_tag = xmlio.reparsed_tag(
        tag_name, tag_converted_abstract, attributes_text=eautils.attr_string(attr_map))
    xmlio.append_minidom_xml_to_elementtree_xml(
        parent, minidom_tag, attributes=attr_map
    )


def set_copyright_information(parent, poa_article):
    if poa_article.license and poa_article.license.copyright_statement:
        copyright_tag = SubElement(parent, "CopyrightInformation")
        copyright_tag.text = poa_article.license.copyright_statement


def convert_research_organism(research_organism):
    # Lower case except for the first letter followed by a dot by a space
    research_organism_converted = research_organism.lower()
    if re.match(r'^[a-z]\. ', research_organism_converted):
        # Upper the first character and add to the remainder
        research_organism_converted = (
            research_organism_converted[0].upper() +
            research_organism_converted[1:])
    return research_organism_converted


def set_object(parent, object_type, params):
    # e.g.  <Object Type="keyword"><Param Name="value">human</Param></Object>
    object_tag = SubElement(parent, "Object")
    object_tag.set("Type", object_type)
    for param_name, param in params.items():
        param_tag = SubElement(object_tag, "Param")
        param_tag.set("Name", param_name)
        param_tag.text = param
    return object_tag


def set_article_type(parent, poa_article):
    "set the object tag holding the article type"
    if poa_article.article_type in ["correction", "retraction"]:
        for related_article in poa_article.related_articles:
            object_type = None
            if related_article.related_article_type == "corrected-article":
                object_type = "Erratum"
            elif related_article.related_article_type == "retracted-article":
                object_type = "Retraction"
            if object_type:
                params = OrderedDict()
                params["type"] = str(related_article.ext_link_type)
                params["id"] = str(related_article.xlink_href)
                set_object(parent, object_type, params)


def set_research_organism(parent, poa_article):
    "research organism object tags"
    for research_organism in poa_article.research_organisms:
        if research_organism.lower() != 'other':
            # Convert the research organism
            research_organism_converted = convert_research_organism(research_organism)
            params = {"value": research_organism_converted}
            set_object(parent, "keyword", params)


def set_categories(parent, poa_article, split_article_categories):
    "set object tags for the categories"
    for article_category in poa_article.article_categories:
        if split_article_categories is True:
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
            set_object(parent, "keyword", params)


def set_grants(parent, poa_article):
    "object tags for funding grants"
    for award in poa_article.funding_awards:
        for award_id in award.award_ids:
            if award.institution_name:
                params = OrderedDict()
                params["id"] = award_id
                params["grantor"] = award.institution_name
                set_object(parent, "grant", params)


def dataset_assigning_authority(uri):
    """precise assigning_authority value considering the uri in some cases"""
    if ASSIGNING_AUTHORITY_URI_MAP and uri:
        for hint, new_value in ASSIGNING_AUTHORITY_URI_MAP.items():
            if hint in uri:
                return new_value


def dataset_details(dataset):
    """
    return assigning_authority and id value for dataset
    consider the uri value, it may change the assigning_authority

    :param dataset: Dataset object
    :returns: string assigning authority of the dataset, string id is the uri or doi
    """
    assigning_authority = dataset_assigning_authority(
        etoolsutils.firstnn([dataset.uri, dataset.doi]))
    id_value = etoolsutils.firstnn([dataset.doi, dataset.accession_id])
    return assigning_authority, id_value


def data_ref_details(ref):
    assigning_authority = None
    id_value = None
    # convert map keys to lower case
    lower_case_map = OrderedDict()
    for key, value in DATA_REF_SOURCE_MAP.items():
        lower_case_map[key.lower()] = value
    # case-insensitive matching of ref source to map key
    if ref.source and ref.source.lower() in lower_case_map.keys():
        assigning_authority = lower_case_map[ref.source.lower()]
        if ref.accession:
            id_value = ref.accession
        elif ref.doi:
            id_value = ref.doi
    return assigning_authority, id_value


def set_datasets(parent, poa_article):
    """object tags for datasets"""
    dataset_objects = []
    for dataset in poa_article.datasets:
        assigning_authority, id_value = dataset_details(dataset)
        if assigning_authority and id_value:
            dataset = OrderedDict([
                ('assigning_authority', assigning_authority),
                ('params', {'id': id_value})
            ])
            dataset_objects.append(dataset)
    # next add from ref list but do not add duplicates
    for ref in [ref for ref in poa_article.ref_list if ref.publication_type == 'data']:
        assigning_authority, id_value = data_ref_details(ref)
        if assigning_authority and id_value:
            dataset = OrderedDict([
                ('assigning_authority', assigning_authority),
                ('params', {'id': id_value})
            ])
            # only add if not a duplicate
            if str(dataset) not in [str(existing_dataset) for existing_dataset in dataset_objects]:
                dataset_objects.append(dataset)

    # set the object tags
    for dataset in dataset_objects:
        set_object(parent, dataset.get('assigning_authority'), dataset.get('params'))


def set_object_list(parent, poa_article, split_article_categories):
    # Keywords and others go in Object tags
    object_list = SubElement(parent, "ObjectList")

    # Add related article data for correction articles
    set_article_type(object_list, poa_article)

    # Add research organisms
    set_research_organism(object_list, poa_article)

    # Add article categories
    set_categories(object_list, poa_article, split_article_categories)

    # Add keywords
    for keyword in poa_article.author_keywords:
        params = {"value": keyword}
        set_object(object_list, "keyword", params)

    # Add grant / funding
    set_grants(object_list, poa_article)

    # Add datasets
    set_datasets(object_list, poa_article)

    # Finally, do not leave an empty ObjectList tag, if present
    if len(object_list) <= 0:
        parent.remove(object_list)


def get_pub_type(poa_article):
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


def build_pubmed_xml(poa_articles, config_section="elife", pub_date=None, add_comment=True):
    """
    Given a list of article article objects
    generate PubMed XML from them
    """
    raw_config = config[config_section]
    pubmed_config = parse_raw_config(raw_config)
    return PubMedXML(poa_articles, pubmed_config, pub_date, add_comment)


def pubmed_xml(poa_articles, config_section="elife", pub_date=None, add_comment=True,
               pretty=False):
    "build PubMed xml and return output as a string"
    p_xml = build_pubmed_xml(poa_articles, config_section, pub_date, add_comment)
    return p_xml.output_xml(pretty=pretty)


def pubmed_xml_to_disk(poa_articles, config_section="elife", pub_date=None, add_comment=True,
                       pretty=False):
    "build pubmed xml and write the output to disk"
    p_xml = build_pubmed_xml(poa_articles, config_section, pub_date, add_comment)
    xml_string = p_xml.output_xml(pretty=pretty)
    # Write to file
    filename = TMP_DIR + os.sep + p_xml.batch_id + '.xml'
    with open(filename, "wb") as open_file:
        open_file.write(xml_string)


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
