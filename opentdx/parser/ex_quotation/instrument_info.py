import struct
from typing import override

from opentdx.parser.baseParser import BaseParser, register_parser


@register_parser(0x4867, 1)
class InstrumentInfo(BaseParser):
    """获取扩展市场商品信息（tdxpy 兼容）"""

    def __init__(self, start: int, count: int = 100):
        self.body = bytearray.fromhex("01 04 48 67 00 01 08 00 08 00 f5 23")
        self.body.extend(struct.pack("<IH", start, count))

    @override
    def deserialize(self, data):
        from collections import OrderedDict

        (header_start, header_count) = struct.unpack("<IH", data[:6])
        pos = 6

        result = []
        for _ in range(header_start):
            entry = data[pos: pos + 64]
            category = entry[0]
            market = entry[1]
            code_raw = entry[4:13]
            name_raw = entry[13:30]
            desc_raw = entry[30:39]

            code = code_raw.split(b"\x00")[0].decode("gbk", errors="ignore")
            name = name_raw.split(b"\x00")[0].decode("gbk", errors="ignore")
            desc = desc_raw.split(b"\x00")[0].decode("gbk", errors="ignore")

            result.append(OrderedDict([
                ("category", category),
                ("market", market),
                ("code", code),
                ("name", name),
                ("desc", desc),
            ]))
            pos += 64

        return result
