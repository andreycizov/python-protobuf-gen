# AUTOGEN: run `protobuf_gen.reflection.generate_pb_core` in order to re-generate

from enum import Enum


class PBType(Enum):
    BOOL = 8
    BYTES = 12
    DOUBLE = 1
    ENUM = 14
    FIXED32 = 7
    FIXED64 = 6
    FLOAT = 2
    GROUP = 10
    INT32 = 5
    INT64 = 3
    MESSAGE = 11
    SFIXED32 = 15
    SFIXED64 = 16
    SINT32 = 17
    SINT64 = 18
    STRING = 9
    UINT32 = 13
    UINT64 = 4


class PBLabel(Enum):
    OPTIONAL = 1
    REPEATED = 3
    REQUIRED = 2
