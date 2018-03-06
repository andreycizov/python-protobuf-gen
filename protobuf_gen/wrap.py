import collections
import os
import random
import shutil
import string
import sys
from collections import __init__
from importlib import import_module
from tempfile import mkdtemp
from typing import List, Dict, Optional, Tuple

from google.protobuf import descriptor_pool, descriptor_database

from protobuf_gen.remap import _build_pb_with_prefix

from protobuf_gen.transpiler import build, BuildProps, InputModule, OutputModule


def _clear_pb_descriptor_database():
    """
    !!! This is a dirty hack, but ensures that tests can both run the compiler and then re-import the files again.
    """
    print('Use c descriptors', descriptor_pool._USE_C_DESCRIPTORS)

    if not descriptor_pool._USE_C_DESCRIPTORS:
        dp = descriptor_pool._DEFAULT

        dp._internal_db = descriptor_database.DescriptorDatabase()
        dp._descriptor_db = None
        dp._descriptors = {}
        dp._enum_descriptors = {}
        dp._service_descriptors = {}
        dp._file_descriptors = {}
        dp._toplevel_extensions = {}
        dp._file_desc_by_toplevel_extension = {}
        dp._extensions_by_name = collections.defaultdict(dict)
        dp._extensions_by_number = collections.defaultdict(dict)
    else:
        pass


def _random_pkg_name():
    return ''.join(random.sample(string.ascii_letters, 16))


def _load_protoc_mods(
    output_files: List[InputModule],
    root_autogen: str,
):
    # we just need to say "map this definition module to a new one"

    output_mods: List[OutputModule] = []
    clear_mods = []

    for of in output_files:
        to_import = root_autogen + '.' + of.mod
        print('Importing', to_import)
        m = import_module(to_import)

        clear_mods.append(m)

        output_mods += [of.to_output(m.DESCRIPTOR)]

    return output_mods


def wrap(
    output_dir_wrappers='./wrappers',
    root_module='example_mod',
    root_autogen='autogen',
    output_files: List[InputModule] = None,
):
    build(
        BuildProps(
            root_module,
            root_autogen,
            _load_protoc_mods(
                output_files,
                root_autogen,
            )
        ),
        outdir=output_dir_wrappers
    )
