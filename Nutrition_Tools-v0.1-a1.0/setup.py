from setuptools import setup, find_packages

setup(
    name='nutrition-tools',
    version='0.1.0a1.0',
    author='tsinglett',
    author_email='NA',
    description='A project that reads a recipe and returns its nutritional content.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests==2.28.1',
        'PyYAML==6.0',
        'fuzzywuzzy==0.18.0',
        'python-Levenshtein==0.20.9',
        'pint==0.20.1',
        'ratelimit==2.2.1',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)