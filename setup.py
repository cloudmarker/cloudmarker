"""Setup script."""

import setuptools

import cloudmarker

_description = cloudmarker.__doc__.splitlines()[0]
_long_description = open('README.rst').read()
_version = cloudmarker.__version__
_requires = open('pkg-requirements.txt').read().splitlines()

setuptools.setup(

    name='cloudmarker',
    version=_version,
    author='Cloudmarker Authors and Contributors',
    description=_description,
    long_description=_long_description,
    url='https://github.com/cloudmarker/cloudmarker',

    install_requires=_requires,

    packages=setuptools.find_packages(exclude=['cloudmarker.test']),

    entry_points={
        'console_scripts': {
            'cloudmarker = cloudmarker.manager:main'
        }
    },

    # Reference for classifiers: https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Monitoring',
    ],

    keywords='cloud security monitoring framework',
)
