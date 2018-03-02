from protobuf_gen.autogen.core import PBType

PBToPy = {
    PBType.BOOL: bool,
    PBType.BYTES: bytes,
    PBType.DOUBLE: float,

    PBType.FIXED32: int,
    PBType.FIXED64: int,
    PBType.FLOAT: float,

    PBType.INT32: int,
    PBType.INT64: int,

    PBType.SFIXED32: int,
    PBType.SFIXED64: int,
    PBType.SINT32: int,
    PBType.SINT64: int,
    PBType.STRING: str,
    PBType.UINT32: int,
    PBType.UINT64: int,
}

ATOMS = (int, float, bytes, str, bool)
