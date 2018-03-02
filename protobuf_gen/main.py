import collections
import os
import random
import shutil
import string
from importlib import import_module
from tempfile import mkdtemp
from typing import Dict, List

from google.protobuf import descriptor_pool, symbol_database, descriptor_database
from grpc_tools.protoc import main as protoc_main

from protobuf_gen.error import TranspilerError
from protobuf_gen.patch import rename_protobuf_imports
from protobuf_gen.transpiler import InputModule, OutputModule, build, BuildProps


def random_name():
    return ''.join(random.sample(string.ascii_letters, 16))
    pass


def build_pb_with_prefix(
    prefix: str,
    protoc_output_dir: str,
    includes: List[str] = None,
    input_proto: List[str] = None,
):
    args = ['__main__']

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
        prefix
    )


def transpile(
    output_dir='.',
    root_module='example_mod',
    root_autogen='autogen',
    includes: List[str] = None,
    input_proto: List[str] = None,
    output_files: Dict[str, InputModule] = None
):
    includes = [] if includes is None else includes
    input_proto = [] if input_proto is None else input_proto
    output_files = {} if output_files is None else output_files

    root_autogen_init = root_autogen

    workdir = mkdtemp()
    workdir_protoc = mkdtemp()

    protoc_output_dir = os.path.join(workdir, root_module, root_autogen)
    protoc_output_dir = os.path.join(workdir_protoc, random_name())

    protoc_output_dir_parent, protoc_output_dir_mod = os.path.split(protoc_output_dir)

    workdir_mod_root = os.path.join(workdir, root_module)

    root_autogen = root_module + '.' + root_autogen

    os.makedirs(protoc_output_dir, exist_ok=True)
    os.makedirs(workdir_mod_root, exist_ok=True)

    try:
        build_pb_with_prefix(
            protoc_output_dir_mod,
            protoc_output_dir,
            includes,
            input_proto
        )

        import sys
        sys.path += [protoc_output_dir_parent]

        # we now need to import all of the modules that have been compiled into the shit!

        output_mods: Dict[str, OutputModule] = {}
        clear_mods = []

        for k, of in output_files.items():
            # to_import = root_autogen + '.' + of.mod
            to_import = protoc_output_dir_mod + '.' + of.mod
            print('Importing', to_import)
            m = import_module(to_import)

            clear_mods.append(m)

            output_mods[k] = of.to_output(m.DESCRIPTOR)

        build(
            BuildProps(
                root_module,
                root_autogen,
                output_mods
            ),
            outdir=workdir_mod_root
        )

        for x in clear_mods:
            del x

        m = import_module(protoc_output_dir_mod)
        del m

        sys.path = [x for x in sys.path if x != workdir]

        print(sys.path)

        def copy_function(a, b):
            print('Copy', a, b)
            return shutil.copy2(a, b)

        with open(os.path.join(workdir_mod_root, '__init__.py'), 'w+') as f_in:
            f_in.write('\n')

        for x in os.walk(protoc_output_dir):
            print('A', x)

        for x in os.walk(workdir_mod_root):
            print('B', x)

        shutil.copytree(workdir_mod_root, output_dir, copy_function=copy_function)

        os.makedirs(os.path.join(output_dir, root_autogen_init))

        build_pb_with_prefix(
            root_autogen,
            os.path.join(output_dir, root_autogen_init),
            includes,
            input_proto
        )

        def clear(self):
            self._internal_db = descriptor_database.DescriptorDatabase()
            self._descriptor_db = None
            self._descriptors = {}
            self._enum_descriptors = {}
            self._service_descriptors = {}
            self._file_descriptors = {}
            self._toplevel_extensions = {}
            # TODO(jieluo): Remove _file_desc_by_toplevel_extension after
            # maybe year 2020 for compatibility issue (with 3.4.1 only).
            self._file_desc_by_toplevel_extension = {}
            # We store extensions in two two-level mappings: The first key is the
            # descriptor of the message being extended, the second key is the extension
            # full name or its tag number.
            self._extensions_by_name = collections.defaultdict(dict)
            self._extensions_by_number = collections.defaultdict(dict)

        clear(descriptor_pool._DEFAULT)
    finally:
        shutil.rmtree(workdir)
