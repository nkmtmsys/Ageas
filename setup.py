import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "Ageas",
    version = "v0.0.1-alpha6",
    author = "nkmtmsys and JackSSK",
    author_email = "gyu17@alumni.jh.edu",
    description = "AutoML-based Genomic fEatrue extrAction System",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/nkmtmsys/Ageas",
    project_urls = {"Bug Tracker": "https://github.com/nkmtmsys/Ageas/issues",},
    packages = setuptools.find_packages(),
    package_data = {'': ['data/config/*', 'data/human/*', 'data/mouse/*']},
    classifiers = [
                    'Programming Language :: Python :: 3',
                    'License :: OSI Approved :: MIT License',
                    'Operating System :: OS Independent',
                    ],
    python_requires = ">=3.6",
    include_package_data = True,
    install_requires = [
        'shap >= 0.40.0',
        'numpy >= 1.19.5',
        'scipy >= 1.8.0',
        'torch >= 1.11.0',
        'pandas >= 1.4.2',
        'netgraph >= 4.4.1',
        'xgboost >= 1.6.0',
        'networkx >= 2.8.1',
        'matplotlib >= 3.5.2',
        'scikit-learn >= 1.0.2',
    ],
)
