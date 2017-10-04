import configparser as configparser
import json

config = configparser.ConfigParser(interpolation=None)
config.read('pubmed.cfg')

def parse_raw_config(raw_config):
    "parse the raw config to something good"
    pubmed_config = {}
    boolean_values = []
    int_values = []
    list_values = []

    int_values.append("year_of_first_volume")

    for value_name in raw_config:
        if value_name in boolean_values:
            pubmed_config[value_name] = raw_config.getboolean(value_name)
        elif value_name in int_values:
            pubmed_config[value_name] = raw_config.getint(value_name)
        elif value_name in list_values:
            pubmed_config[value_name] = json.loads(raw_config.get(value_name))
        else:
            # default
            pubmed_config[value_name] = raw_config.get(value_name)
    return pubmed_config
