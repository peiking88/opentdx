import struct
from typing import override

from opentdx.const import MARKET, PERIOD, ADJUST
from opentdx.parser.baseParser import BaseParser, register_parser
from opentdx.utils.help import get_price, to_datetime


@register_parser(0x523)
class K_Line(BaseParser):
    def __init__(self, market: MARKET, code: str, period: PERIOD, times: int = 1, start: int = 0, count: int = 800, adjust: ADJUST= ADJUST.NONE):
        self.body = struct.pack('<H6sHHHHH8s', market.value, code.encode('gbk'), period.value, times, start, count, adjust.value, b'')
        
        self.period = period
        
    @override
    def deserialize(self, data):
        data_len = len(data)
        count, = struct.unpack('<H', data[:2])
        pos = 2

        minute_category = self.period.value < 4 or self.period.value == 7 or self.period.value == 8

        # 每个 bar 最小需要: 4(date) + 1(min OHLC) + 8(vol/amount) = 13 字节
        MIN_BAR_BYTES = 13

        bars = []
        for _ in range(count):
            if pos + MIN_BAR_BYTES > data_len:
                break
            date_num, = struct.unpack('<I', data[pos: pos + 4])
            pos += 4
            date_time = to_datetime(date_num, minute_category)

            # 逐个读取 OHLC，每步前检查是否还有足够空间（至少 1 字节价格 + 8 字节 vol）
            if pos + 9 > data_len:
                break
            open, pos = get_price(data, pos)
            if pos + 9 > data_len:
                break
            close, pos = get_price(data, pos)
            if pos + 9 > data_len:
                break
            high, pos = get_price(data, pos)
            if pos + 9 > data_len:
                break
            low, pos = get_price(data, pos)

            if pos + 8 > data_len:
                break
            vol, amount = struct.unpack('<ff', data[pos: pos + 8])
            pos += 8

            upCount = 0
            downCount = 0
            # 智能检测：试探后续 4 字节是否为 upCount/downCount 还是下一行日期
            if pos + 4 <= data_len:
                try_date, = struct.unpack('<I', data[pos: pos + 4])
                if minute_category:
                    # 分钟线日期是紧凑编码，不能用 YYYYMMDD 格式判断
                    # 用 to_datetime 解码，若得到的时间在当前 bar 之后则是下一根 bar
                    try_date_time = to_datetime(try_date, minute_category)
                    if try_date_time <= date_time:
                        upCount, downCount = struct.unpack('<HH', data[pos: pos + 4])
                        pos += 4
                else:
                    y, m, d = try_date // 10000, (try_date % 10000) // 100, try_date % 100
                    if y < 1990 or m < 1 or m > 12 or d < 1 or d > 31:
                        upCount, downCount = struct.unpack('<HH', data[pos: pos + 4])
                        pos += 4
                    else:
                        try_date_time = to_datetime(try_date, minute_category)
                        if try_date_time <= date_time:
                            upCount, downCount = struct.unpack('<HH', data[pos: pos + 4])
                            pos += 4

            bar = {
                'datetime': date_time,
                'open': open,
                'close': close,
                'high': high,
                'low': low,
                'vol': vol,
                'amount': amount,
            }
            if upCount != 0 or downCount != 0:
                bar['up_count'] = upCount
                bar['down_count'] = downCount
            bars.append(bar)
            
        return bars