from elifepubmed import generate
import time

if __name__ == '__main__':
    default_pub_date = time.strptime("2017-07-17 07:17:07", "%Y-%m-%d %H:%M:%S")
    xml_files = []

    xml_files.append(['tests/test_data/elife-00666.xml', 'elife', default_pub_date, False])
    xml_files.append(['tests/test_data/elife-02935-v2.xml', 'elife', default_pub_date, False])
    xml_files.append(['tests/test_data/elife-15743-v1.xml', 'elife', default_pub_date, False])
    xml_files.append(['tests/test_data/elife_poa_e00003.xml', 'elife', default_pub_date, False])
    xml_files.append(['tests/test_data/elife_poa_e12717.xml', 'elife', default_pub_date, False])
    xml_files.append(['tests/test_data/bmjopen-4-e003269.xml', 'bmjopen', default_pub_date, False])
    xml_files.append(['tests/test_data/pb369-jats.xml', 'pb', default_pub_date, False])

    for xml_file, config_section, pub_date, add_comment in xml_files:
        generate.TMP_DIR = 'tests/test_data'
        articles = generate.build_articles_for_pubmed(
            article_xmls=[xml_file], config_section=config_section)
        generate.pubmed_xml_to_disk(articles, config_section, pub_date, add_comment)
