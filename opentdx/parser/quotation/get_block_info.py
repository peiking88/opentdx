import struct
from typing import override

from opentdx.parser.baseParser import BaseParser, register_parser
from opentdx.utils.block_reader import BlockReader, BlockReader_TYPE_FLAT


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


def get_and_parse_block_info(client, block_file):
    """下载并解析板块（tdxpy 兼容）"""
    from opentdx.parser.quotation.get_block_info import BlockInfoMeta, BlockInfo

    meta = client.call(BlockInfoMeta(block_file))
    size = meta["size"]

    chunk_size = 0x7530
    chunks = (size + chunk_size - 1) // chunk_size

    content = bytearray()
    for i in range(chunks):
        response = client.call(BlockInfo(block_file, i * chunk_size, min(chunk_size, size - i * chunk_size)))
        content.extend(response)

    return BlockReader.get_data(content, BlockReader_TYPE_FLAT)
