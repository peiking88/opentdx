import struct
from typing import override

from opentdx.parser.baseParser import BaseParser, register_parser


@register_parser(0x1869)
class BlockInfoMeta(BaseParser):
    """获取板块元信息（tdxpy 兼容）"""

    def __init__(self, block_file: str):
        raw_block_file = block_file.encode("utf-8") if isinstance(block_file, str) else block_file
        self.body = raw_block_file.ljust(0x28, b"\x00")

    @override
    def deserialize(self, data):
        size, _, hash_value, _ = struct.unpack("<I1s32s1s", data)
        return {"size": size, "hash_value": hash_value}


@register_parser(0x186a)
class BlockInfo(BaseParser):
    """获取板块内容（tdxpy 兼容）"""

    def __init__(self, block_file: str, start: int, size: int):
        raw_block_file = block_file.encode("utf-8") if isinstance(block_file, str) else block_file
        self.body = struct.pack("<II", start, size) + raw_block_file.ljust(0x64, b"\x00")

    @override
    def deserialize(self, data):
        return data[4:]

