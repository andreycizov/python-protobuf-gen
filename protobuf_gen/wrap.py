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
    includes: List[str],
    input_proto: List[str],
    output_files: Dict[str, InputModule],
    workdir: str = None,
    pkg: str = None,
    existing=False
):
    if workdir is None:
        workdir = mkdtemp()
    if pkg is None:
        pkg = _random_pkg_name()

    protoc_output_dir = os.path.join(workdir, pkg.replace('.', '/'))

    os.makedirs(protoc_output_dir, exist_ok=True)

    try:
        sys.path = sys.path + [os.path.join(workdir)]

        if not existing:

            _build_pb_with_prefix(
                pkg,
                protoc_output_dir,
                includes,
                input_proto
            )

        output_mods: Dict[str, OutputModule] = {}
        clear_mods = []

        print('Workdir', workdir)

        for k, of in output_files.items():
            to_import = pkg + '.' + of.mod
            print('Importing', to_import)
            m = import_module(to_import)

            clear_mods.append(m)

            output_mods[k] = of.to_output(m.DESCRIPTOR)

        if not existing:
            _clear_pb_descriptor_database()

        return output_mods
    finally:
        sys.path = [x for x in sys.path if x != workdir]

        if not existing:
            shutil.rmtree(workdir)


def wrap(
    output_dir_wrappers='./wrappers',
    root_module='example_mod',
    root_autogen='autogen',
    includes: List[str] = None,
    input_proto: List[str] = None,
    output_files: Dict[str, InputModule] = None,
    existing: Optional[Tuple[str, str]] = None
):
    build(
        BuildProps(
            root_module,
            root_autogen,
            _load_protoc_mods(
                includes,
                input_proto,
                output_files,
                *(existing + (True,) if existing else (None, None, False))
            )
        ),
        outdir=output_dir_wrappers
    )
