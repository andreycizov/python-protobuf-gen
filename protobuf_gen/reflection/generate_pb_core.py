import os

from google.protobuf.descriptor import FieldDescriptor


def generate_header():
    x = "protobuf_gen.reflection.generate_pb_core"

    return f"""# AUTOGEN: run `{x}` in order to re-generate

from enum import Enum

"""


def generate_type_enum():
    TYPE_ = 'TYPE_'
    a = [(x[len(TYPE_):], getattr(FieldDescriptor, x)) for x in dir(FieldDescriptor) if x.startswith(TYPE_)]

    r = '''
class PBType(Enum):
'''
    for k, v in a:
        r += f'    {k} = {v}\n'
    return r


def generate_label_enum():
    TYPE_ = 'LABEL_'
    a = [(x[len(TYPE_):], getattr(FieldDescriptor, x)) for x in dir(FieldDescriptor) if x.startswith(TYPE_)]

    r = '''
class PBLabel(Enum):
'''
    for k, v in a:
        r += f'    {k} = {v}\n'
    return r


if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(__file__), '..', 'autogen', 'core.py'), 'w+') as f_in:
        f_in.write(generate_header())
        f_in.write(generate_type_enum())
        f_in.write('\n')
        f_in.write(generate_label_enum())
