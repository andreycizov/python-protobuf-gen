import re
import os
import sys
from typing import NamedTuple, Dict, Tuple, List, Union

from google.protobuf.descriptor import FileDescriptor

# these modules are provided as part of the standard python protobuf distribution by google and therefore are
# not required.
DO_NO_REPLACE = [
    'google.protobuf',
]


def rename_protobuf_imports(dir_root, root, do_not_replace=DO_NO_REPLACE):
    pattern = r'^from ([^ ]+) import ([^ ]+)_pb2 as ([^ ]+)__pb2$'
    pattern = re.compile(pattern)

    for path, _, files in os.walk(dir_root):
        init_file = os.path.join(path, '__init__.py')

        if not os.path.exists(init_file):
            with open(init_file, 'w+'):
                pass

        for file in files:
            if not file.endswith('.py'):
                continue

            with open(os.path.join(path, file), 'r') as f:
                lines = list(f.readlines())

            changes = 0

            with open(os.path.join(path, file), 'w+') as f:
                for line in lines:
                    match = pattern.match(line)
                    if match and match.group(1) not in do_not_replace:
                        changes += 1
                        f.write(f'from {root}.{match.group(1)} import {match.group(2)}_pb2 as {match.group(3)}__pb2\n')
                    else:
                        f.write(line)

            print('Patched', file, changes)


class ServiceMethodPatch(NamedTuple):
    service: str
    method: str

    client_streaming: bool = False
    server_streaming: bool = False


PatchList = List[Union[ServiceMethodPatch]]


def patch_file(f: FileDescriptor, patch_defn: PatchList):
    for patch in patch_defn:
        if isinstance(patch, ServiceMethodPatch):
            x = f.services_by_name[patch.service].methods_by_name[patch.method]

            if patch.client_streaming:
                x.client_streaming = True

            if patch.server_streaming:
                x.server_streaming = True
        else:
            raise NotImplementedError(repr(patch))


if __name__ == '__main__':
    rename_protobuf_imports(*sys.argv[1:])
