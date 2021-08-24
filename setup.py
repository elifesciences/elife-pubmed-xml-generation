from setuptools import setup

import elifepubmed

with open("README.md") as fp:
    readme = fp.read()

setup(
    name="elifepubmed",
    version=elifepubmed.__version__,
    description="eLife PubMed deposit of journal articles.",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=["elifepubmed"],
    license="MIT",
    install_requires=["elifetools", "elifearticle", "configparser", "PyYAML"],
    url="https://github.com/elifesciences/elife-pubmed-xml-generation",
    maintainer="eLife Sciences Publications Ltd.",
    maintainer_email="tech-team@elifesciences.org",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
