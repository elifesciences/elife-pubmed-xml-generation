import configparser as configparser
import json
import yaml

config = configparser.ConfigParser(interpolation=None)
config.read("pubmed.cfg")


def parse_raw_config(raw_config):
    "parse the raw config to something good"
    pubmed_config = {}
    boolean_values = []
    int_values = []
    list_values = []
    yaml_values = []

    boolean_values.append("split_article_categories")
    int_values.append("year_of_first_volume")
    list_values.append("pub_date_types")
    list_values.append("author_contrib_types")
    list_values.append("history_date_types")
    list_values.append("remove_tags")
    list_values.append("abstract_label_types")
    yaml_values.append("publication_types")

    for value_name in raw_config:
        if value_name in boolean_values:
            pubmed_config[value_name] = raw_config.getboolean(value_name)
        elif value_name in int_values:
            pubmed_config[value_name] = raw_config.getint(value_name)
        elif value_name in list_values:
            pubmed_config[value_name] = json.loads(raw_config.get(value_name))
        elif value_name in yaml_values:
            with open(raw_config.get(value_name), "rb") as yaml_file:
                pubmed_config[value_name] = yaml.load(
                    yaml_file.read(), Loader=yaml.FullLoader
                )
        else:
            # default
            pubmed_config[value_name] = raw_config.get(value_name)
    return pubmed_config
