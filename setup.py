from setuptools import setup, find_packages

setup(
    name='rake',
    version='0.1',
    author='Eddie Dane',
    packages=find_packages(),
    install_requires=[
        'PyYAML',
        'pandas',
        'playwright',
        'colorama',
        'tabulate',
        'python-slugify',
        'click',
    ],
    entry_points={
        'console_scripts': [
            'rakestart=rake.cli:main',
        ],
    },
)
