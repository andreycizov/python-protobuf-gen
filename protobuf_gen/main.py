from typing import Dict, List

from protobuf_gen.remap import remap
from protobuf_gen.transpiler import InputModule
from protobuf_gen.wrap import wrap


def transpile(
    output_dir_wrappers='.',
    output_dir_autogen='.',
    root_autogen='example_mod.autogen',
    includes: List[str] = None,
    input_proto: List[str] = None,
    output_files: List[InputModule] = None
):
    remap(
        output_dir_autogen,
        root_autogen,
        includes,
        input_proto
    )

    import sys
    sys.path += [
        output_dir_autogen
    ]

    wrap(
        output_dir_wrappers,
        root_autogen,
        output_files,
    )
