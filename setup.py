from setuptools import setup

import elifepubmed

with open('README.rst') as fp:
    README = fp.read()

setup(
    name='elifepubmed',
    version=elifepubmed.__version__,
    description='eLife PubMed deposit of journal articles.',
    long_description=README,
    packages=['elifepubmed'],
    license='MIT',
    install_requires=[
        "elifetools",
        "elifearticle",
        "GitPython",
        "configparser",
        "PyYAML"
    ],
    url='https://github.com/elifesciences/elife-pubmed-xml-generation',
    maintainer='eLife Sciences Publications Ltd.',
    maintainer_email='py@elifesciences.org',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        ]
    )
