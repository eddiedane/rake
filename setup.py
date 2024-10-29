from setuptools import setup, find_packages
import pypandoc

setup(
    name='rake-python',
    version='0.1.9',
    author='Eddie Dane',
    description='Rake is a simple yet powerful web scraping tool that allows you to configure and execute complex and repetitive scraping tasks with ease and little to no code.',
    long_description=pypandoc.convert_file('README.md', 'rst'),
    long_description_content_type='text/x-rst',
    url='https://github.com/eddiedane/rake',
    packages=find_packages(),
    install_requires=[
        'PyYAML',
        'pandas',
        'playwright',
        'colorama',
        'tabulate',
        'python-slugify',
        'click',
        'openpyxl',
        'pypandoc'
    ],
    entry_points={
        'console_scripts': [
            'rakestart=rake.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
