"""
There's much in terms of cleaning to be done, but it works correctly
"""

import os
from collections import defaultdict
from typing import Iterable, Dict, Set, Tuple, Optional, NamedTuple, List

from google.protobuf.descriptor import FileDescriptor, Descriptor, FieldDescriptor, EnumDescriptor, EnumValueDescriptor, \
    ServiceDescriptor, MethodDescriptor, _NestedDescriptorBase

from protobuf_gen.patch import PatchList, patch_file
from protobuf_gen.const import PBToPy
from protobuf_gen.autogen.core import PBLabel, PBType


def _map_proto_to_module(name: str):
    return name.replace('/', '.').replace('.proto', '_pb2')


def _map_file(d: FileDescriptor):
    return _map_proto_to_module(d.name)


class InputModule:
    def __init__(
        self,
        cannonical_name: str,
        filename: str,
        patches: PatchList = None
    ):
        self.cannonical_name = cannonical_name
        self.filename = filename
        self.patches = [] if patches is None else patches

    @property
    def mod(self):
        return _map_proto_to_module(self.filename)

    def to_output(self, desc: FileDescriptor):
        return OutputModule(self.cannonical_name, desc, self.patches)


class OutputModule:
    def __init__(
        self,
        cannonical_name: str,
        descriptor: FileDescriptor,
        patches: PatchList = None
    ):
        """
        Definition of an output module
        :param descriptor: DESCRIPTOR attribute of the protobuf auto-generated _pb2.py module
        :param patches: a list of patches to be applied to the module
        """
        self.module_name = cannonical_name
        self.descriptor = descriptor
        self.patches = [] if patches is None else patches


class BuildProps:
    def __init__(
        self,
        absolute_autogen_name: str = '',
        output_mods: List[OutputModule] = None,
    ):
        """
        :param absolute_autogen_name: the absolute name of the
        :param output_mods:
        """
        self.prefix_autogen = absolute_autogen_name
        self.output_mods = [] if output_mods is None else output_mods


class BuildContext:
    def __init__(
        self,
        props: BuildProps,
        reqs: Dict[str, Set[str]] = None,
    ):
        self.props = props
        self.reqs = defaultdict(set) if reqs is None else reqs

    @property
    def map(self):
        return self.props.output_mods

    @property
    def prefix_autogen(self):
        return self.props.prefix_autogen

    def get_absolute_name_3(self, y: _NestedDescriptorBase):
        r = []
        x = y
        while x is not None:
            r.append(x.name)
            x = x.containing_type
        r.append(self.prefix_autogen + '.' + _map_file(y.file))

        # print(r)

        return reversed(r)

    def get_absolute_name(self, y: _NestedDescriptorBase):
        r = []
        x = y
        while x is not None:
            r.append(x.name)
            x = x.containing_type
        r.append(self.prefix_autogen + '.' + _map_file(y.file))

        alias = self.add_absolute_requirement(r[-1])

        return alias + '.' + '.'.join(reversed(r[:-1]))

    def get_file_absolute(self, f: FileDescriptor):
        z: Optional[Tuple[str, str]]
        z = None

        for v in self.map:
            if v.descriptor == f:
                z = (v.module_name, v.descriptor)
                break

        assert z is not None, f'{f.name} needs a map'

        return z

    def get_absolute_name_2(self, y: _NestedDescriptorBase):
        r = []
        x = y
        while x is not None:
            r.append(x.name)
            x = x.containing_type

        abs_map, _ = self.get_file_absolute(y.file)

        r.append(abs_map)

        # alias = self.add_absolute_requirement(r[-1])

        return r[-1], '.'.join(reversed(r[:-1]))

    def _ancestors(self, x: _NestedDescriptorBase):
        y = x
        r = []
        while y is not None:
            r.append(y)
            y = y.containing_type
        return list(reversed(r))

    def _prefix(self, a, b):
        r = []
        for x, y in zip(a, b):
            if x == y:
                r.append(x)
            else:
                break
        return r

    def get_absolute_name_mapped(self, against: _NestedDescriptorBase, to: _NestedDescriptorBase) -> Tuple[bool, str]:
        x, y = self.get_absolute_name_2(to)

        if against == to:
            return False, '.'.join(y.split('.')[1:])
        elif against.file == to.file:

            aa = self._ancestors(against)
            ab = self._ancestors(to)

            shared_prefix = self._prefix(aa, ab)
            # print('in the middle', [x.name for x in aa], [x.name for x in ab], [x.name for x in shared_prefix], y)

            prfx = self._prefix([x.name for x in shared_prefix], y.split('.'))

            # find catch up in the middle
            r = y.split('.')[len(prfx):]
            # print('aaa', r)
            return len(prfx) == 0, '.'.join(r)
        else:
            px, cx = x.rsplit('.', maxsplit=1)

            self.reqs[px].add(cx)

            return True, cx + '.' + y

    def add_absolute_requirement(self, req: str):
        y, x = req.rsplit('.', 1)

        self.reqs[y].add(x)
        return x


def prepend_level(xs: str) -> str:
    return '\n'.join(['    ' + s for s in xs.split('\n')])


def build_field(ctx: BuildContext, d: Descriptor, f: FieldDescriptor):
    lbl = PBLabel(f.label)
    is_optional = lbl == PBLabel.OPTIONAL
    is_list = lbl == PBLabel.REPEATED

    type_label = PBType(f.type)

    default_val = repr(f.default_value)
    is_abs = True

    # so a name is either a string that could be written to the code and would

    if type_label == PBType.ENUM:
        et: EnumDescriptor
        et = f.enum_type

        if PBLabel.REPEATED != lbl:

            zyxel: EnumValueDescriptor
            zyxel = et.values_by_number[f.default_value]

            enum_type: EnumDescriptor
            enum_type = zyxel.type

            is_abs, domain_zzz = ctx.get_absolute_name_mapped(d, enum_type)

            # print(domain_zzz)

            default_val = domain_zzz + '.' + zyxel.name

        # how to map a against something

        is_abs, type_name_unquot = ctx.get_absolute_name_mapped(d, et)
        type_name = f"'{type_name_unquot}'"

        if PBLabel.REPEATED == lbl:
            type_name_unquot = f'List[{"cls." if not is_abs else ""}{type_name_unquot}]'
            type_name = f'List[{type_name}]'
        elif not is_abs:
            type_name_unquot = f'cls.{type_name_unquot}'
    elif type_label == PBType.MESSAGE:
        mt: Descriptor
        mt = f.message_type

        is_abs, type_name_unquot = ctx.get_absolute_name_mapped(d, mt)
        type_name = f"'{type_name_unquot}'"

        if f.default_value is None:
            type_name = f'Optional[{type_name}]'

        if PBLabel.REPEATED == lbl:
            type_name_unquot = f'List[{"cls." if not is_abs else ""}{type_name_unquot}]'
            type_name = f'List[{type_name}]'
        elif not is_abs:
            type_name_unquot = f'cls.{type_name_unquot}'
    elif type_label == PBType.GROUP:
        assert False
    else:
        type_name_unquot = PBToPy.get(PBType(f.type)).__name__
        type_name = type_name_unquot

        if PBLabel.REPEATED == lbl:
            type_name_unquot = f'List[{type_name_unquot}]'
            type_name = f'List[{type_name}]'

    if PBLabel.OPTIONAL == lbl:
        # type_name = f'Optional[{type_name}]'
        pass
    elif PBLabel.REPEATED == lbl:
        pass
    else:
        assert False, lbl

    return f.name, type_name, default_val, type_name_unquot, is_abs


def build_message(ctx: BuildContext, d: Descriptor) -> str:
    ctx.add_absolute_requirement('protobuf_gen.abstract.Message')

    nested_types: Iterable[Descriptor]
    nested_types = d.nested_types

    nts = []

    for f in nested_types:
        nts += [prepend_level(build_message(ctx, f))]

    nt_str = '\n\n'.join(nts)

    enum_types: Iterable[EnumDescriptor]
    enum_types = d.enum_types

    ets = []

    for f in enum_types:
        ets += [prepend_level(build_enum(ctx, f))]

    et_str = '\n\n'.join(ets)

    fields: Iterable[FieldDescriptor]
    fields = d.fields

    fields_defined = []

    for f in sorted(fields, key=lambda x: x.number):
        f_def = build_field(ctx, d, f)

        fields_defined.append(f_def + (f,))

        # fs += [
        #     f"    {f.name}: {type_name} = {repr(f.default_value)}"
        # ]

    init_args = [
        'self'
    ]

    init_body = []

    slots_body = []

    get_slot_types_body = []

    for a, b, c, c_unquot, c_is_abs, wi in fields_defined:
        def_val_mut = wi.default_value == []

        c = c if not def_val_mut else None

        init_args.append(f'{a}: {b} = {c}')

        to_val = a if not def_val_mut else f'{wi.default_value} if {a} is None else {a}'

        init_body.append(f'self.{a} = {to_val}')

        get_slot_types_body.append(f'{c_unquot}')

        slots_body.append(repr(a))

    slots_body_str = ', '.join(slots_body)

    get_slot_types_body_str = ', '.join(get_slot_types_body)

    init_args_str = ',\n        '.join(init_args)
    init_body_str = '\n        '.join(init_body) if len(init_body) else 'pass'

    init_str = f"""    def __init__(
        {init_args_str}
    ):
        {init_body_str}"""

    f_str = init_str
    f2_str = f"""    @classmethod
    def get_slot_types(cls):
        return [{get_slot_types_body_str}]"""

    abs_name = ctx.get_absolute_name(d)

    out = [
        prepend_level(f'pb_cls = {abs_name}'),
        prepend_level(f'__slots__ = [{slots_body_str}]'),
        nt_str,
        et_str,
        f_str,
        f2_str,
    ]

    out = [x for x in out if len(x)]

    if len(out) == 0:
        out = [prepend_level('pass')]

    out_str = '\n\n'.join(out)

    return f"""class {d.name}(Message):
{out_str}"""


def build_enum(ctx: BuildContext, d: EnumDescriptor) -> str:
    r = []

    enum_abs_name = ctx.get_absolute_name(d)

    values: Iterable[EnumValueDescriptor]
    values = d.values

    for v in sorted(values, key=lambda x: x.number):
        req = v.number
        r.append(f'    {v.name} = {req}')
        pass

    r = '\n'.join(r)

    return f"""class {d.name}(Enum):
{r}"""


def build_deps(deps: Dict[str, Set[str]]) -> str:
    r = []

    for k, deps in deps.items():
        deps = ', '.join(deps)
        r.append(f'from {k} import {deps}')

    return '\n'.join(r)


def build_service(ctx: BuildContext, s: ServiceDescriptor) -> str:
    methods: Iterable[MethodDescriptor]
    methods = s.methods

    ms = []

    a, b = ctx.get_absolute_name_3(s)
    stub_name = f'{a}_grpc.{b}Stub'

    ms += [f"    stub_cls = {stub_name.split('.')[-1]}"]

    ctx.add_absolute_requirement(stub_name)

    ctx.add_absolute_requirement('protobuf_gen.abstract.Service')

    for method in methods:
        client_streaming = getattr(method, 'client_streaming', False)
        server_streaming = getattr(method, 'server_streaming', False)

        _, input_type = ctx.get_absolute_name_mapped(s, method.input_type) if method.input_type else None
        _, output_type = ctx.get_absolute_name_mapped(s, method.output_type) if method.output_type else None

        output_type_bare = output_type

        input_type = f'Iterable[{input_type}]' if input_type and client_streaming else input_type
        output_type = f'Iterable[{output_type}]' if output_type and server_streaming else output_type

        input_type_str = f"arg: '{input_type}'" if input_type else ''
        output_type_str = f" -> '{output_type}'" if output_type else ''

        if input_type and client_streaming:
            behaviour = f'self.stub.{method.name}((x.to_pb() for x in arg))'
        elif input_type:
            behaviour = f'self.stub.{method.name}(arg.to_pb())'
        else:
            behaviour = f'self.stub.{method.name}()'

        if output_type and server_streaming:
            behaviour = f'return ({output_type_bare}.from_pb(x) for x in {behaviour})'
        elif output_type:
            behaviour = f'return {output_type_bare}.from_pb({behaviour})'
        else:
            behaviour = f'{behaviour}'

        M = f"""    def {method.name}(self, {input_type_str}){output_type_str}:
        {behaviour}"""
        ms.append(M)
        # print('\t' * de, f.full_name, f.name, ref_type(f.input_type), ref_type(f.output_type), client_streaming,
        #       server_streaming)

    ms_str = '\n\n'.join(ms) if len(ms) else '    pass'

    return f"""class {s.name}(Service):
{ms_str}"""


def build_file(context: BuildContext, d: FileDescriptor) -> str:
    '''
    We would like to map things. Which of the things should be directly mapped, and which ones should be just provided
    '''

    r = '# Enums'

    enums: Iterable[EnumDescriptor]
    enums = d.enum_types_by_name.values()

    enums_its = []

    for enum in enums:
        enums_its += [build_enum(context, enum)]

    # enums_str = '\n'.join(enums_its)

    messages: Iterable[Descriptor]
    messages = d.message_types_by_name.values()

    msgs = []

    for msg in messages:
        msgs += [build_message(context, msg)]

    services: Iterable[ServiceDescriptor]
    services = d.services_by_name.values()

    srvcs = []

    for srvc in services:
        srvcs += [build_service(context, srvc)]

    # msgs_str = '\n'.join(msgs)

    # deps = {k: [b for a, b in v] for k, v in
    #         groupby(sorted((x, y) for x, y in (x.rsplit('.', 1) for dep, alias in context.reqs.items())), key=lambda x: x[0])}

    deps = build_deps(context.reqs)

    items = [deps]

    items += ['# Enums'] + enums_its if len(enums_its) else []
    items += ['# Messages'] + msgs if len(msgs) else []
    items += ['# Services'] + srvcs if len(srvcs) else []

    items_str = '\n\n\n'.join(items)

    return f"""# AUTOGENERATED
from typing import NamedTuple, List, Optional, Iterable
from enum import Enum

{items_str}
"""


def build(props: BuildProps, outdir='./'):
    for v in props.output_mods:

        patch_file(v.descriptor, v.patches)

        file_str = build_file(BuildContext(props), v.descriptor)

        file_name = os.path.join(outdir, v.module_name.replace('.', '/') + '.py')
        file_bts = file_str.encode()

        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        with open(file_name, 'w+b') as f_in:
            f_in.write(file_bts)

        print(f'Written {file_name}: {len(file_bts)} bytes')
