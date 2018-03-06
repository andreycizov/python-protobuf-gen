import random
import string
from importlib import import_module
from typing import List

from protobuf_gen.transpiler import build, BuildProps, InputModule, OutputModule


def _load_protoc_mods(
    output_files: List[InputModule],
    root_autogen: str,
):
    # we just need to say "map this definition module to a new one"

    output_mods: List[OutputModule] = []
    clear_mods = []

    for of in output_files:
        to_import = root_autogen + '.' + of.mod

        m = import_module(to_import)

        clear_mods.append(m)

        output_mods += [of.to_output(m.DESCRIPTOR)]

    return output_mods


def wrap(
    output_dir_wrappers='./wrappers',
    root_autogen='autogen',
    output_files: List[InputModule] = None,
):
    build(
        BuildProps(
            root_autogen,
            _load_protoc_mods(
                output_files,
                root_autogen,
            )
        ),
        outdir=output_dir_wrappers
    )
