import os
from argparse import ArgumentParser
from typing import List

import pkg_resources
from grpc_tools.protoc import main as protoc_main

from protobuf_gen.error import TranspilerError
from protobuf_gen.patch import rename_protobuf_imports


def arguments(args: ArgumentParser):
    args.add_argument(
        '-R',
        '--root',
        dest='root_autogen',
        default='new_root.autogen',
        help='the new root module name for re-mapped protobuf assets',
    )

    args.add_argument(
        '-O',
        '--output',
        dest='output_dir_autogen',
        default='.',
        help='the output directory given the protoc',
    )

    args.add_argument(
        '-I',
        '--include',
        dest='includes',
        action='append',
        default=[],
        help='Add an include to be provided to protoc',
    )

    args.add_argument(
        dest='input_proto',
        action='append',
        default=[],
        help='Add an include to be provided to protoc',
    )


def _build_pb_with_prefix(
    module_prefix: str,
    root_output_dir: str,
    includes: List[str] = None,
    input_proto: List[str] = None,
):
    protoc_output_dir = os.path.join(root_output_dir, module_prefix.replace('.', '/'))
    os.makedirs(protoc_output_dir, exist_ok=True)

    args = ['__main__']

    includes = [pkg_resources.resource_filename('grpc_tools', '_proto')] + includes

    args += ['-I' + x for x in includes]

    args += [
        '--python_out=' + protoc_output_dir,
        '--grpc_python_out=' + protoc_output_dir,
    ]

    args += [x for x in input_proto]

    r = protoc_main(
        args
    )

    if r != 0:
        raise TranspilerError(f'protoc returned {r}, check tool output')

    rename_protobuf_imports(
        protoc_output_dir,
        module_prefix
    )


def remap(
    output_dir_autogen='./autogen',
    root_autogen='new_root.autogen',
    includes: List[str] = None,
    input_proto: List[str] = None,
):
    """
    Root remapping utility for protobuf.

    :param root_autogen: the new root module name for re-mapped protobuf assets
    :param output_dir_autogen: the output directory given the protoc
    :param includes: list of includes that should be provided to protoc
    :param input_proto:
    :return:
    """
    _build_pb_with_prefix(
        root_autogen,
        output_dir_autogen,
        includes,
        input_proto
    )
