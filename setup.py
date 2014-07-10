from setuptools import setup, find_packages


setup(
    name='connectedAFRICA',
    version='0.1',
    description="Politically exposed persons in South Africa",
    long_description=None,
    classifiers=[],
    keywords='',
    author='Friedrich Lindenberg',
    author_email='info@connectedafrica.org',
    url='https://github.com/codeforafrica/connectedAFRICA',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    zip_safe=False,
    install_requires=[
        "granoloader>=0.1",
        "grano-client>=0.2.4",
        "gunicorn==19.0",
        "Fabric==1.9.0",
        "Flask==0.10.1",
        "Flask-Assets==0.10",
        "Flask-Script==2.0.5",
        "Flask-FlatPages==0.5",
        "lxml==3.3.5",
        "PyYAML==3.10",
        "thready>=0.1.4",
        "unicodecsv==0.9.4",
        "cssmin==0.2.0",
        "networkx==1.9",
        "python-slugify>=0.0.7"
    ],
    tests_require=[],
    entry_points=""" """,
)
