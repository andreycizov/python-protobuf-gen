from typing import Dict, List

from protobuf_gen.remap import remap
from protobuf_gen.transpiler import InputModule
from protobuf_gen.wrap import wrap


def transpile(
    output_dir_wrappers='./wrappers',
    output_dir_autogen='./autogen',
    root_module='example_mod',
    root_autogen='autogen',
    includes: List[str] = None,
    input_proto: List[str] = None,
    output_files: Dict[str, InputModule] = None
):
    remap(
        output_dir_autogen,
        root_autogen,
        includes,
        input_proto
    )

    wrap(
        output_dir_wrappers,
        root_module,
        root_autogen,
        includes,
        input_proto,
        output_files
    )
