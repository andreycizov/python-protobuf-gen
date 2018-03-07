============
protobuf-gen
============

.. image:: https://img.shields.io/pypi/v/protobuf-gen.svg
        :target: https://pypi.python.org/pypi/protobuf-gen

.. image:: https://img.shields.io/travis/andreycizov/python-protobuf-gen.svg
        :target: https://travis-ci.org/andreycizov/python-protobuf-gen

.. image:: https://readthedocs.org/projects/protobuf-gen/badge/?version=latest
        :target: https://protobuf-gen.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/andreycizov/python-protobuf-gen/shield.svg
        :target: https://pyup.io/repos/github/andreycizov/python-protobuf-gen/
        :alt: Updates

.. image:: https://codecov.io/gh/andreycizov/python-protobuf-gen/coverage.svg?branch=master
        :target: https://codecov.io/gh/andreycizov/python-protobuf-gen/?branch=master

Motivation
----------

This is a library to generate type-hinted protocol buffer bindings. This tool solves two main issues with the original
Google cproto compiler python output:

- cproto does not support exporting the code with the package roots that are different from what had been supplied
  by the original .proto file authors, therefore expecting the protocol users to sed through the code (see issues
  `881 <https://github.com/google/protobuf/issues/881>`_ and `1491 <https://github.com/google/protobuf/issues/1491>`_).
- It builds the interfaces at run time, therefore disallowing one from using the static type checkers and disabling
  the auto-complete in your favourite IDE.

Example
_______

This example is usable for building a fully-functional etcd3 client in python. Otherwise see `tests <./tests>`_.

Let's start by cloning the repositories containing the necessary .proto files to be compiled. Etcd3 references files
from several protobuf libraries, so we are going to need all of them.

.. code-block:: sh

    mkdir pb-includes

    # etcd references it's own .proto files against the root of their own repository, so the doubling here is intended
    git clone https://github.com/coreos/etcd.git ./pb-includes/etcd/etcd

    git clone https://github.com/grpc-ecosystem/grpc-gateway.git ./pb-includes/grpc-gateway
    git clone https://github.com/gogo/protobuf.git ./pb-includes/protobuf


Now, let's actually generate the files.


.. code-block:: python

    from protobuf_gen import remap, wrap

    # all of the _pb2 modules will now be importable through `etcd3py.pb_mods.*`
    # for example a module "google/api/http.proto" will be available as "etcd3py.pb_mods.google.api.http_pb2"
    remap(
        # the working directory is given as the parent directory of the package folder (etcd3py in this case).
        '.',
        'etcd3py.pb_mods,
        # .proto include directories
        [
            './pb-includes/grpc-gateway/third_party/googleapis',
            './pb-includes/etcd',
            './pb-includes/protobuf',
        ],
        # .proto files to be included in the distribution
        [
            'etcd/etcdserver/etcdserverpb/rpc.proto',
            'etcd/mvcc/mvccpb/kv.proto',
            'etcd/auth/authpb/auth.proto',

            'google/api/annotations.proto',
            'gogoproto/gogo.proto',
            'google/api/http.proto',
        ]
    )


Author
------
Andrey Cizov (acizov@gmail.com), 2018