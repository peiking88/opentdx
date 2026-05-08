import struct
from typing import override

from opentdx.parser.baseParser import BaseParser, register_parser
from opentdx.utils.helper import get_datetime


@register_parser(0x3892, 1)
class HistoryInstrumentBarsRange(BaseParser):
    """获取扩展市场K线范围（tdxpy 兼容）"""

    def __init__(self, market: int, code: str, start: int, end: int, seq_id: int = 1):
        raw_code = code.encode("utf-8") if isinstance(code, str) else code
        self.body = struct.pack("<B9s", market, raw_code.ljust(9, b"\x00"))
        self.body += struct.pack("<H", 7)
        self.body += struct.pack("<II", start, end)

    @override
    def deserialize(self, data):
        from collections import OrderedDict

        pos = 12
        (ret_count,) = struct.unpack("<H", data[pos: pos + 2])
        pos += 2

        result = []
        for _ in range(ret_count):
            (d1, d2) = struct.unpack("<HH", data[pos: pos + 4])
            year, month, day = get_datetime(4, data, pos)[:3]
            pos += 4

            open_price, high, low, close = struct.unpack("<ffff", data[pos: pos + 16])
            pos += 16

            position, trade, settlementprice = struct.unpack("<IIf", data[pos: pos + 12])
            pos += 12

            result.append(OrderedDict([
                ("datetime", f"{year:04d}-{month:02d}-{day:02d}"),
                ("year", year),
                ("month", month),
                ("day", day),
                ("hour", 0),
                ("minute", 0),
                ("open", round(open_price, 2)),
                ("high", round(high, 2)),
                ("low", round(low, 2)),
                ("close", round(close, 2)),
                ("position", int(position)),
                ("trade", int(trade)),
                ("settlementprice", round(settlementprice, 2)),
            ]))

        return result
