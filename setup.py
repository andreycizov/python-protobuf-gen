from setuptools import setup, find_packages

import protobuf_gen as pkg

readme = open('README.rst').read()
history = open('HISTORY.rst').read()

setup(
    name=pkg.__name__,
    version=pkg.__version__,
    author=pkg.__author__,
    author_email=pkg.__email__,
    packages=find_packages(include=(pkg.__name__,)),
    description='Python 3 type hinted protobuf binding generator',
    keywords='',
    include_package_data=True,
    long_description=readme,
    install_requires=[
        'grpcio>=1.2.0',
        'grpcio_tools',
        'protobuf',
    ],
    test_suite='tests',
    tests_require=[

    ],
)
