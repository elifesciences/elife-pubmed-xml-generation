# elife-pubmed-xml-generation

Generate PubMed deposit of journal articles.

Using JATS XML file as input, this library can generate a PubMed deposit XML file. The XML is parsed using the module from a different library, `elifearticle`, to extract the data from the XML file and to populate the objects defined in `elifearticle`.

It would be possible, with some additional code, to populate the `elifearticle` with data from a different data source and still generate a PubMed deposit, if all or a portion of the data is not stored in JATS XML format.

The PubMed deposit file will include the following output if the data is available in the `elifearticle` objects:

- Journal (journal title, publisher name, issn, volume, issue, pub date)
- Article metadata (title, doi, pii, language, pub date, abstract, copyright, keywords)
- Authors, group authors, author affiliations
- Funding data
- `aheadofprint` publishing status

It is possible to generate a PubMed deposit XML which includes one article or mulitple articles, depending on how many articles are in the list when generating the output.

Some sample input and output files can be found in the `tests/test_data/` folder, which are the basis for the automated tests.

## Requirements and install

a) Install from `pypi` package index

```
pip install elifepubmed
```

b) Install locally

Clone the git repo

`git clone https://github.com/elifesciences/elife-pubmed-xml-generation.git`

Create a python virtual environment and activate it

```
python3 -m venv venv
source venv/bin/activate
```

Install it locally

```
pip install -r requirements.txt
python setup.py install
```

## Configuration

The `pubmed.cfg` configuration file provided in this repository can be changed in order to read slightly different JATS XML attributes, depending on the journal.

The `publication_types.yaml` file, referenced in the `pubmed.cfg` file, is where a JATS XML article type value can be mapped to a PubMed `publication_type` value.

## Example usage

This library is meant to be integrated into another operational system, however the following are examples using interactive Python:

Example 1 - Convert a test fixture XML to elifearticle Article() object, then generate PubMed XML

```
>>> from letterparser import generate
>>> articles = generate.build_articles_for_pubmed(["tests/test_data/elife-00666.xml"])
>>> p_xml = generate.pubmed_xml(articles)
>>> print(p_xml)
```

Example 2 - Convert a test fixture XML to elifearticle Article() object, set the article `is_poa` property, then generate PubMed XML, the output XML will contain `<PubDate PubStatus="aheadofprint">`

```
>>> from letterparser import generate
>>> articles = generate.build_articles_for_pubmed(["tests/test_data/elife-00666.xml"])
>>> articles[0].is_poa = True
>>> p_xml = generate.pubmed_xml(articles)
>>> print(p_xml)
```

Example 3 - Convert two test fixture XML files to elifearticle Article() objects, then generate PubMed XML to disk, the output will be written in the local `tmp/` folder

```
>>> from letterparser import generate
>>> articles = generate.build_articles_for_pubmed(["tests/test_data/elife-00666.xml", "tests/test_data/elife-02935-v2.xml"])
>>> generate.pubmed_xml_to_disk(articles)
```

## Run code tests

Use `pytest` for testing, install it if missing:

```
pip install pytest
```

Run tests

```
pytest
```

Run tests with `coverage` (install it if missing)

```
coverage run -m pytest
```

then report on code coverage

```
coverage report -m
```

## License

Licensed under [MIT](https://opensource.org/licenses/mit-license.php).
