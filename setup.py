from setuptools import setup, find_packages
from codecs import open
from os import path

import gnss_tec

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gnss-tec',

    description='Total electron content reconstruction using GNSS data',
    long_description=long_description,

    version=gnss_tec.__version__,

    url='https://github.com/gnss-lab/gnss-tec',

    author=gnss_tec.__author__,
    author_email=gnss_tec.__email__,

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',

        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='ionosphere gnss tec development',

    packages=find_packages(exclude=['docs', 'tests']),

    include_package_data=True,

    install_requires=[],

    python_requires='>=3',

    extras_require={
        'test': [
            'pytest',
            'coverage',
        ],
    },
)
