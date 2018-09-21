from setuptools import setup, find_packages


setup(
    name='Siyazana',
    version='0.1',
    description="Politically exposed persons in South Africa",
    long_description=None,
    classifiers=[],
    keywords='',
    author='Code for Africa',
    author_email='support@codeforafrica.org',
    url='https://github.com/ANCIR/siyazana.co.za',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    zip_safe=False,
    install_requires=[
        "granoloader",
        "grano-client",
        "gunicorn>=19.0",
        "Fabric>=1.9.0",
        "Flask>=0.12.2",
        "Flask-Assets>=0.12",
        "Flask-Script>=2.0.5",
        "Flask-FlatPages>=0.5",
        "Flask-Caching>=0.13.1",
        "lxml>=3.3.5",
        "PyYAML>=3.12",
        "thready>=0.1.4",
        "unicodecsv>=0.9.4",
        "cssmin>=0.2.0",
        "networkx>=1.9",
        "python-slugify>=0.0.7",
        "python-Levenshtein>=0.11.2",
        "scrapekit>=0.0.1",
        "apikit>=0.0.1",
        "Unidecode>=0.04.16"
    ],
    dependency_links=[
        "https://github.com/ANCIR/granoloader/tarball/master#egg=granoloader",
        "https://github.com/ANCIR/grano-client/tarball/master#egg=grano-client",
    ],
    tests_require=[],
    entry_points=""" """,
)
