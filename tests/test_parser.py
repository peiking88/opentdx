"""Parser 单元测试 — 用构造的二进制数据测试解析器反序列化逻辑，无需服务器连接。

本文件测试边界条件和数据格式解析的正确性，与真实服务端集成测试互补。
真实服务端往返测试见 test_quotation_client.py / test_ex_quotation_client.py / test_mac_quotation_client.py
"""
import struct
from datetime import date, time

import pandas as pd
import pytest

from opentdx.const import EX_MARKET, MARKET
from opentdx.parser.baseParser import BaseParser
from opentdx.utils.help import get_price
from opentdx.exceptions import ValidationException


def _run_deserialize(parser: BaseParser, payload: bytes) -> object:
    return parser.deserialize(payload)


# ──────────────────────────────────────────────
# ex_quotation/goods.py
# ──────────────────────────────────────────────

class TestF23F6:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.goods import F23F6
        count = 2
        data = struct.pack('<IH', 0, count)
        for _ in range(count):
            data += struct.pack('<B8sB12H', 0, b'TST\x00\x00\x00\x00\x00', 0, *([0] * 12))
        result = _run_deserialize(F23F6(), data)
        assert result is None


class TestF2487:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.goods import F2487

        # 构造够大的 data 让解析器不报错
        # 格式: market(B) + code(23s) = 24, 然后 active..price(32), vol..amount(12), a(16), padding to 164, b
        market = EX_MARKET.HK_MAIN_BOARD.value
        code_bytes = b'00700'.ljust(23, b'\x00')
        data = bytearray()
        data += struct.pack('<B23s', market, code_bytes)
        data += struct.pack('<I7f', 1, 350.0, 355.0, 360.0, 345.0, 352.0, 0.0, 352.0)
        data += struct.pack('<IIf', 10000000, 5000, 500000.0)
        data += struct.pack('<4I', 0, 0, 0, 0)
        data += b'\x00' * (164 - 68 - 16)
        data += struct.pack('<HII24fB10fHB', 0, 0, 0, *([0.0] * 24), 0, *([0.0] * 10), 0, 0)

        result = _run_deserialize(F2487(EX_MARKET.HK_MAIN_BOARD, '00700'), bytes(data))
        assert isinstance(result, dict)
        assert result['code'] == '00700'


class TestF2562:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.goods import F2562
        count = 1
        data = struct.pack('<H', count)
        # 每条: H(2) + 23s(23) + H(2) + I(4) + B(1) + fffHH(4*3+2+2=16) = 48
        item = struct.pack('<H23sHIBfffHH', 1, b'TGOODS\x00' * 2 + b'\x00' * 9, 0, 100, 1, 1.0, 2.0, 3.0, 0, 0)
        data += item

        result = _run_deserialize(F2562(0, 0, 600), data)
        assert isinstance(result, list)
        assert len(result) == 1


# ──────────────────────────────────────────────
# mac_quotation/file_query.py
# ──────────────────────────────────────────────

class TestFileList:
    def test_deserialize(self):
        from opentdx.parser.mac_quotation.file_query import FileList
        hash_bytes = b'a' * 32
        data = struct.pack('<IIb32s', 0, 4096, 1, hash_bytes)
        result = _run_deserialize(FileList('test.dat'), data)
        assert result['offset'] == 0
        assert result['size'] == 4096
        assert result['flag'] == 1


class TestFileDownload:
    def test_deserialize(self):
        from opentdx.parser.mac_quotation.file_query import FileDownload
        content = 'hello world'.encode('gbk')
        data = struct.pack('<II', 1, len(content)) + content
        result = _run_deserialize(FileDownload('test.dat'), data)
        assert result['index'] == 1
        assert result['size'] == len(content)
        assert result['content'] == 'hello world'

    def test_deserialize_short_data(self):
        from opentdx.parser.mac_quotation.file_query import FileDownload
        result = _run_deserialize(FileDownload('test.dat'), b'short')
        assert result is None

    def test_deserialize_non_gbk(self):
        from opentdx.parser.mac_quotation.file_query import FileDownload
        content = bytes([0xFF, 0xFE, 0x00, 0x01])
        data = struct.pack('<II', 1, len(content)) + content
        result = _run_deserialize(FileDownload('test.dat'), data)
        assert result is not None
        assert result['index'] == 1


# ──────────────────────────────────────────────
# mac_quotation/symbol_info.py
# ──────────────────────────────────────────────

class TestSymbolInfo:
    def test_deserialize(self):
        from opentdx.parser.mac_quotation.symbol_info import SymbolInfo

        # symbol_info.py reads: at offset 8: market(H) + code(22s) + name(44s)
        # then at offset 96: date_raw(I) + time_raw(I) + activity(I) + pre_close..close(5f)
        #   + momentum(f) + vol(I) + amount(f) + inside_volume(I) + outside_volume(I)
        # then at offset 148: decimal(H) + a(I) + b(f) + c(f) + 20x + vr(I) + turnover(f) + avg(f)
        name_enc = '平安银行'.encode('gbk')
        name_bytes = name_enc.ljust(44, b'\x00')
        code_bytes = b'000001'.ljust(22, b'\x00')

        data = b'\x00' * 8
        data += struct.pack('<H22s44s', MARKET.SZ.value, code_bytes, name_bytes)
        data += b'\x00' * (96 - 8 - 68)
        data += struct.pack('<III5ffIfII',
                            20260508, 150000, 100,
                            12.0, 12.5, 13.0, 11.8, 12.3,
                            0.3, 50000000, 6000000.0, 25000000, 25000000)
        data += struct.pack('<HI2f20xI2f', 2, 0, 0.0, 0.0, 1, 2.5, 12.15)

        result = _run_deserialize(SymbolInfo(MARKET.SZ, '000001'), data)
        assert isinstance(result, dict)
        assert result['code'] == '000001'
        assert result['name'] == '平安银行'
        assert result['market'] == MARKET.SZ
        assert result['pre_close'] == 12.0
        assert result['open'] == 12.5


# ──────────────────────────────────────────────
# quotation/stock.py
# ──────────────────────────────────────────────

class TestF452:
    def test_deserialize(self):
        from opentdx.parser.quotation.stock import f452
        count = 2
        data = struct.pack('<H', count)
        data += struct.pack('<BIff', MARKET.SZ.value, 1, 10.5, 11.0)
        data += struct.pack('<BIff', MARKET.SH.value, 600000, 8.0, 8.5)

        result = _run_deserialize(f452(0, 2), data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['market'] == MARKET.SZ
        assert result[1]['market'] == MARKET.SH
        assert result[1]['code'] == '600000'


# ──────────────────────────────────────────────
# quotation/quotes_encrypt.py
# ──────────────────────────────────────────────

class TestQuotesEncrypt:
    def test_constructor_empty_raises(self):
        from opentdx.parser.quotation.quotes_encrypt import QuotesEncrypt
        with pytest.raises(ValidationException, match='count'):
            QuotesEncrypt([])

    def test_constructor_with_stocks(self):
        from opentdx.parser.quotation.quotes_encrypt import QuotesEncrypt
        parser = QuotesEncrypt([(MARKET.SZ, '000001')])
        assert parser.msg_id == 0x547

    def test_deserialize_single_stock(self):
        from opentdx.parser.quotation.quotes_encrypt import QuotesEncrypt

        count = 1
        raw = bytearray()
        raw.extend(struct.pack('<H', count))
        raw.extend(struct.pack('<B6sH', MARKET.SZ.value, b'000001', 100))

        def enc_price(v):
            raw.append(v & 0x7F)

        enc_price(12)  # close
        enc_price(0)   # pre_close diff
        enc_price(1)   # open diff
        enc_price(3)   # high diff
        enc_price(-1)  # low diff

        raw.extend(struct.pack('<I', 150000))
        enc_price(0)
        enc_price(50)
        enc_price(10)

        raw.extend(struct.pack('<f', 60000.0))
        enc_price(25)
        enc_price(25)
        enc_price(10)
        enc_price(5)

        for _ in range(5):
            enc_price(0)
            enc_price(0)
            enc_price(10)
            enc_price(10)

        raw.extend(struct.pack('<HII', 0, 0, 0))

        for _ in range(24):
            enc_price(0)

        encrypted = bytes(b ^ 0x93 for b in raw)

        result = _run_deserialize(QuotesEncrypt([(MARKET.SZ, '000001')]), encrypted)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['code'] == '000001'
        assert result[0]['market'] == MARKET.SZ
        assert 'handicap' in result[0]
        assert len(result[0]['handicap']['bid']) == 5
        assert len(result[0]['handicap']['ask']) == 5


# ──────────────────────────────────────────────
# quotation/list2.py
# ──────────────────────────────────────────────

class TestList2:
    def test_deserialize(self):
        from opentdx.parser.quotation.list2 import List2
        count = 1
        data = struct.pack('<H', count)
        # 29=6+2+8+2+2+1+1+4+2+2=... let me count: 6+2=8, +8=16, +2=18, +2=20, +2=22, +1=23, +4=27, +2=29
        # <6sH8sHHHBfHH = 9 items
        item = struct.pack('<6sH8sHHBfHH',
                           b'000001', 1000, b'PAYH\x00\x00\x00\x00', 0, 0, 2, 12.5, 0, 0)
        data += item

        result = _run_deserialize(List2(MARKET.SZ, 0), data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['code'] == '000001'
        assert result[0]['decimal_point'] == 2


# ──────────────────────────────────────────────
# quotation/history_transaction_with_trans.py
# ──────────────────────────────────────────────

class TestHistoryTransactionWithTrans:
    def test_deserialize(self):
        from opentdx.parser.quotation.history_transaction_with_trans import HistoryTransactionWithTrans

        count = 2
        data = struct.pack('<Hf', count, 10.0)
        data += struct.pack('<H', 570) + b'\x01' + b'\x01' + b'\x01' + struct.pack('<H', 0)
        data += struct.pack('<H', 571) + b'\x02' + b'\x01' + b'\x01' + struct.pack('<H', 1)

        result = _run_deserialize(
            HistoryTransactionWithTrans(MARKET.SZ, '000001', date(2026, 5, 8), 0, 2),
            data
        )
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['time'] == time(9, 30)
        assert result[0]['action'] == 'BUY'
        assert result[1]['action'] == 'SELL'


# ──────────────────────────────────────────────
# mac_quotation/symbol_auction.py
# ──────────────────────────────────────────────

class TestAuctionParser:
    def test_deserialize(self):
        from opentdx.parser.mac_quotation.symbol_auction import Auction

        count = 2
        code_bytes = b'000001'.ljust(22, b'\x00')
        data = struct.pack('<H22sI', MARKET.SZ.value, code_bytes, count)
        data += b'\x00' * (36 - 28)
        data += struct.pack('<IfIi', 34200, 12.5, 1000, 500)
        data += struct.pack('<IfIi', 34260, 12.6, 2000, 300)

        result = _run_deserialize(Auction(MARKET.SZ, '000001'), data)
        assert 'items' in result
        assert len(result['items']) == 2
        assert result['items'][0]['price'] == 12.5
        assert result['items'][0]['matched'] == 1000
        assert result['code'] == '000001'


# ──────────────────────────────────────────────
# mac_quotation/symbol_tick_charts.py
# ──────────────────────────────────────────────

class TestTickChartsParser:
    def test_deserialize(self):
        from opentdx.parser.mac_quotation.symbol_tick_charts import TickCharts

        code_bytes = b'000001'.ljust(22, b'\x00')
        days = 1
        data = struct.pack('<H22s', MARKET.SZ.value, code_bytes)
        data += struct.pack('<5I5f', 20260508, 0, 0, 0, 0, 12.0, 0.0, 0.0, 0.0, 0.0)
        page_size = 2
        data += struct.pack('<HBHH', days, 0, page_size, page_size)

        for _ in range(days):
            for t in range(page_size):
                data += struct.pack('<HffHH', 570 + t, 12.0, 11.98, 1000, 0)

        name_enc = '平安银行'.encode('gbk')
        name_bytes = name_enc.ljust(44, b'\x00')

        trailing = struct.pack('<44sBHf5x2I5ffIf12x2fI',
                               name_bytes,
                               2, 0, 100.0,
                               20260508, 150000,
                               12.0, 12.5, 13.0, 11.8, 12.3,
                               0.3, 50000000, 6000000.0, 2.5, 12.15, 0)
        data += trailing

        result = _run_deserialize(TickCharts(MARKET.SZ, '000001'), data)
        assert 'charts' in result
        assert len(result['charts']) == days
        assert result['code'] == '000001'


# ──────────────────────────────────────────────
# quotation/get_block_info.py
# ──────────────────────────────────────────────

class TestBlockInfoMeta:
    def test_deserialize(self):
        from opentdx.parser.quotation.get_block_info import BlockInfoMeta
        data = struct.pack('<I1s32s1s', 4096, b'\x00', b'x' * 32, b'\x00')
        result = _run_deserialize(BlockInfoMeta('block_gn.dat'), data)
        assert result['size'] == 4096


class TestBlockInfo:
    def test_deserialize(self):
        from opentdx.parser.quotation.get_block_info import BlockInfo
        raw_content = b'BLOCKDATA\x00\x01\x02\x03'
        data = struct.pack('<I', len(raw_content)) + raw_content
        result = _run_deserialize(BlockInfo('block_gn.dat', 0, 4096), data)
        assert result == raw_content


# ──────────────────────────────────────────────
# quotation/history_tick_chart.py
# ──────────────────────────────────────────────

class TestHistoryTickChartParser:
    def test_deserialize(self):
        from opentdx.parser.quotation.history_tick_chart import HistoryTickChart

        count = 1
        data = struct.pack('<HII', count, 0, 0)
        data += b'\x01' + b'\x01' + b'\x01' + b'\x00' * 10

        result = _run_deserialize(HistoryTickChart(MARKET.SZ, '000001', date(2026, 5, 8)), data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert 'price' in result[0]
        assert 'vol' in result[0]


# ──────────────────────────────────────────────
# bitmap.py 额外测试
# ──────────────────────────────────────────────

class TestBitmapExtra:
    def test_preset_field_basic_is_tuple(self):
        from opentdx.utils.bitmap import PresetField
        assert isinstance(PresetField.BASIC.value, tuple)
        assert len(PresetField.BASIC.value) > 0

    def test_field_selection_construct(self):
        from opentdx.utils.bitmap import FieldSelection, FieldBit
        sel = FieldSelection(FieldBit.PRE_CLOSE, FieldBit.OPEN, FieldBit.CLOSE)
        assert isinstance(sel, FieldSelection)
        assert len(sel) == 3

    def test_field_selection_add(self):
        from opentdx.utils.bitmap import FieldSelection, FieldBit, PresetField
        sel = PresetField.BASIC + FieldBit.AH_CODE
        assert isinstance(sel, FieldSelection)
        assert len(sel) >= 6  # BASIC (6) + AH_CODE (1) = 7, but there may be overlap

    def test_field_selection_or(self):
        from opentdx.utils.bitmap import FieldSelection, PresetField
        sel = PresetField.BASIC | PresetField.QUOTE
        assert isinstance(sel, FieldSelection)
        assert len(sel) >= 6

    def test_field_selection_iter(self):
        from opentdx.utils.bitmap import FieldBit, FieldSelection
        sel = FieldSelection(FieldBit.CLOSE)
        bits = list(sel)
        assert FieldBit.CLOSE in bits

    def test_field_bit_values(self):
        from opentdx.utils.bitmap import FieldBit
        assert FieldBit.PRE_CLOSE == 0
        assert FieldBit.CLOSE == 4
        assert FieldBit.VOL == 5

    def test_get_active_fields_from_bitmap(self):
        from opentdx.utils.bitmap import get_active_fields_from_bitmap, build_bitmap, FieldBit
        bitmap = build_bitmap([FieldBit.PRE_CLOSE, FieldBit.CLOSE])
        active = get_active_fields_from_bitmap(bytes(bitmap))
        assert FieldBit.PRE_CLOSE in active
        assert FieldBit.CLOSE in active

    def test_build_bitmap_preset(self):
        from opentdx.utils.bitmap import build_bitmap, PresetField
        bitmap = build_bitmap(PresetField.BASIC)
        assert len(bitmap) > 0


# ──────────────────────────────────────────────
# helper.py 额外覆盖
# ──────────────────────────────────────────────

class TestHelperExtra:
    def test_get_price_multi_byte(self):
        # 位7 (0x80) 表示更多字节
        data = bytearray([0x80, 0x01])
        price, pos = get_price(data, 0)
        assert price == 64  # 0x01 << 6
        assert pos == 2

    def test_get_price_zero(self):
        data = bytearray([0x00])
        price, pos = get_price(data, 0)
        assert price == 0
        assert pos == 1

    def test_get_price_sign(self):
        # 0x40 设置表示负数
        data = bytearray([0x41])
        price, pos = get_price(data, 0)
        assert price == -1


# ──────────────────────────────────────────────
# help.py 额外覆盖
# ──────────────────────────────────────────────

class TestHelpExtra:
    def test_to_datetime(self):
        from opentdx.utils.help import to_datetime
        dt = to_datetime(20240601)
        assert dt.year == 2024

    def test_exchange_board_code(self):
        from opentdx.utils.help import exchange_board_code
        result = exchange_board_code('HK0287')
        assert isinstance(result, int)

    def test_format_time(self):
        from opentdx.utils.help import format_time
        result = format_time(0)
        assert result == '00:00:00.000'


class TestHelpExtraMore:
    def test_industry_to_board_symbol(self):
        from opentdx.utils.help import industry_to_board_symbol
        result = industry_to_board_symbol(0)
        assert result == ''
        result2 = industry_to_board_symbol(0x00010001)
        assert isinstance(result2, str)

    def test_combine_to_datetime(self):
        from opentdx.utils.help import combine_to_datetime
        dt = combine_to_datetime(20260508, 54000)
        assert dt.year == 2026
        assert dt.month == 5
        assert dt.day == 8
        assert dt.hour == 15
        assert dt.minute == 0

    def test_combine_to_datetime_early_hours(self):
        from opentdx.utils.help import combine_to_datetime
        dt = combine_to_datetime(20260508, 3600, format_tdx_time=True)
        assert dt.hour == 1


    def test_ah_code_to_symbol(self):
        from opentdx.utils.help import ah_code_to_symbol
        result = ah_code_to_symbol(0, 0)
        assert result == ''
        result2 = ah_code_to_symbol(0x06066, MARKET.SZ.value)
        assert isinstance(result2, str)

    def test_lot_size_to_symbol(self):
        from opentdx.utils.help import lot_size_to_symbol
        result = lot_size_to_symbol(100)
        assert isinstance(result, str)


# ──────────────────────────────────────────────
# block_reader.py 测试
# ──────────────────────────────────────────────

class TestBlockReader:
    def test_get_data_flat(self):
        from opentdx.utils.block_reader import BlockReader, BlockReader_TYPE_FLAT

        data = bytearray(384)
        data += struct.pack('<H', 1)  # num blocks
        data += b'BLKNAME\x00\x00'  # blockname (exactly 9 bytes)
        data += struct.pack('<HH', 2, 1)  # stock_count=2, block_type=1
        data += b'000001\x00'  # code (7 bytes)
        data += b'600000\x00'  # code (7 bytes)
        # pad: data so far after 384 = 2+9+4+14 = 29, need 2800
        data += b'\x00' * (2800 - 14)

        reader = BlockReader()
        result = reader.get_data(data, BlockReader_TYPE_FLAT)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_data_group(self):
        from opentdx.utils.block_reader import BlockReader, BlockReader_TYPE_GROUP

        data = bytearray(384)
        data += struct.pack('<H', 1)
        data += b'BLKNAME\x00\x00'
        data += struct.pack('<HH', 1, 0)
        data += b'000001\x00'
        data += b'\x00' * (2800 - 7)

        reader = BlockReader()
        result = reader.get_data(data, BlockReader_TYPE_GROUP)
        assert isinstance(result, list)
        assert len(result) == 1
        assert '000001' in result[0]['code_list']


# ──────────────────────────────────────────────
# base_reader.py 额外覆盖
# ──────────────────────────────────────────────

class TestBaseReaderExtra:
    def test_unpack_records_exception(self):
        from opentdx.utils.base_reader import BaseReader
        reader = BaseReader()
        with pytest.raises(NotImplementedError):
            reader.get_df('test')


# ──────────────────────────────────────────────
# cache.py 额外覆盖
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
# quotation/server.py — 67% 覆盖
# ──────────────────────────────────────────────

class TestServerParsers:
    def test_exchange_announcement(self):
        from opentdx.parser.quotation.server import ExchangeAnnouncement
        data = struct.pack('<B', 1) + 'test announce'.encode('gbk')
        result = _run_deserialize(ExchangeAnnouncement(), data)
        assert result['v'] == 1
        assert 'content' in result

    def test_heartbeat(self):
        from opentdx.parser.quotation.server import HeartBeat
        data = struct.pack('<6sI', b'\x00' * 6, 20260508)
        result = _run_deserialize(HeartBeat(), data)
        assert result == 20260508

    def test_announcement_no_content(self):
        from opentdx.parser.quotation.server import Announcement
        data = struct.pack('<B', 0)
        result = _run_deserialize(Announcement(), data)
        assert result is None

    def test_upgrade_tip_no_msg(self):
        from opentdx.parser.quotation.server import UpgradeTip
        data = struct.pack('<BH50s5s120s', 0, 0, b'\x00' * 50, b'\x00' * 5, b'\x00' * 120)
        result = _run_deserialize(UpgradeTip(), data)
        assert result['had'] == 0
        assert result['msg'] is None

    def test_todo_fde(self):
        from opentdx.parser.quotation.server import TodoFDE
        data = struct.pack('<IH165s16s', 0, 0, b'\x00' * 165, b'\x00' * 16)
        result = _run_deserialize(TodoFDE(), data)
        assert 'unknown' in result


# ──────────────────────────────────────────────
# baseStockClient.py 工具函数测试
# ──────────────────────────────────────────────

class TestBaseStockClientUtil:
    def test_normalize_code_list_single(self):
        from opentdx.client.baseStockClient import _normalize_code_list
        result = _normalize_code_list(1, '000001')
        assert result == [(1, '000001')]

    def test_normalize_code_list_tuple(self):
        from opentdx.client.baseStockClient import _normalize_code_list
        result = _normalize_code_list((1, '000001'))
        assert result == [(1, '000001')]

    def test_normalize_code_list_multi(self):
        from opentdx.client.baseStockClient import _normalize_code_list
        result = _normalize_code_list([(1, '000001'), (2, '600000')])
        assert len(result) == 2


# ──────────────────────────────────────────────
# ex_quotation/kline2.py — 56% 覆盖
# ──────────────────────────────────────────────

class TestKLine2:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.kline2 import K_Line2
        from opentdx.const import EX_MARKET, PERIOD

        count = 1
        header = struct.pack('<B23sHHIIIH', 74, b'TSLA'.ljust(23, b'\x00'), PERIOD.DAILY.value, 1, 0, 0, 0, count)
        # each bar: I(4) + f(4)*7 = 32 bytes
        bar = struct.pack('<IfffffII', 20260508, 250.0, 255.0, 245.0, 252.0, 500000.0, 1000000, 0)
        data = header + bar

        result = _run_deserialize(K_Line2(EX_MARKET.US_STOCK, 'TSLA', PERIOD.DAILY), data)
        assert isinstance(result, list)
        assert len(result) == count


# ──────────────────────────────────────────────
# ex_quotation/table.py — 62% 覆盖
# ──────────────────────────────────────────────

class TestTable:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.table import Table
        data = b'\x00' * 35 + struct.pack('<I', 0) + b'\x00' * (161 - 39)
        data += struct.pack('<II', 1, 10)
        data += 'test content'.encode('gbk')

        result = _run_deserialize(Table(), data)
        assert isinstance(result, tuple)
        assert len(result) == 3


# ──────────────────────────────────────────────
# ex_quotation/history_bars_range.py — 32% 覆盖
# ──────────────────────────────────────────────

class TestHistoryInstrumentBarsRange:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.history_bars_range import HistoryInstrumentBarsRange

        count = 1
        data = b'\x00' * 12 + struct.pack('<H', count)
        # each row: d1(H)+d2(H)=4, open+f*4=16, position+I=4+trade+I=4+settlement=4 = 32
        data += struct.pack('<HH', 0, 0)  # d1, d2 (compressed date)
        data += struct.pack('<ffff', 250.0, 255.0, 245.0, 252.0)
        data += struct.pack('<IIf', 1000, 5000, 251.0)
        data += b'\x00' * 20  # extra padding for get_datetime safety

        result = _run_deserialize(HistoryInstrumentBarsRange(74, 'TSLA', 20260401, 20260501), data)
        assert isinstance(result, list)
        assert len(result) == count


# ──────────────────────────────────────────────
# ex_quotation/instrument_info.py — 30% 覆盖
# ──────────────────────────────────────────────

class TestInstrumentInfoParser:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.instrument_info import InstrumentInfo

        count = 1
        data = struct.pack('<IH', count, 0)
        # each entry: 64 bytes
        entry = bytearray(64)
        entry[0] = 1  # category
        entry[1] = 74  # market
        entry[4:13] = b'TSLA\x00\x00\x00\x00\x00'  # code
        entry[13:30] = 'Tesla Inc'.encode('gbk').ljust(17, b'\x00')
        entry[30:39] = 'EV maker'.encode('gbk').ljust(9, b'\x00')
        data += bytes(entry)

        result = _run_deserialize(InstrumentInfo(0, 1), data)
        assert isinstance(result, list)
        assert len(result) == count
        assert result[0]['code'] == 'TSLA'


# ──────────────────────────────────────────────
# ex_quotation/history_tick_chart.py — 56% 覆盖
# ──────────────────────────────────────────────

class TestExHistoryTickChart:
    def test_deserialize(self):
        from opentdx.parser.ex_quotation.history_tick_chart import HistoryTickChart
        from datetime import date

        count = 1
        # header: B + 23s + I + f + I + I + H = 42 bytes
        data = struct.pack('<B23sIfIIH', 74, b'TSLA'.ljust(23, b'\x00'), 20260508, 250.0, 0, 0, count)
        # bar: H + f + f + I + I = 18 bytes
        data += struct.pack('<HffII', 570, 252.0, 251.5, 1000, 0)

        result = _run_deserialize(HistoryTickChart(EX_MARKET.US_STOCK, 'TSLA', date(2026, 5, 8)), data)
        assert isinstance(result, list)
        assert len(result) == count


# ──────────────────────────────────────────────
# symbol_belong_board.py — 88% 覆盖
# ──────────────────────────────────────────────

class TestSymbolBelongBoard:
    def test_deserialize(self):
        from opentdx.parser.mac_quotation.symbol_belong_board import SymbolBelongBoard
        import json

        data = struct.pack('<H12s5x8s', MARKET.SZ.value, b'Stock_GLHQ\x00\x00\x00\x00\x00', b'\x00' * 8)
        json_data = json.dumps([["GN", 1, "880761", "半导体", 12.5, 12.0, "3", "1", "0.8"]])
        data += json_data.encode('gbk')

        result = _run_deserialize(SymbolBelongBoard('000001', MARKET.SZ), data)
        assert isinstance(result, pd.DataFrame)


class TestCache:
    def test_simple_cache_basic(self):
        from opentdx.utils.cache import SimpleCache
        cache = SimpleCache(ttl_seconds=3600)
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
        cache.delete('key1')
        assert cache.get('key1') is None

    def test_simple_cache_clear(self):
        from opentdx.utils.cache import SimpleCache
        cache = SimpleCache()
        cache.set('a', 1)
        cache.set('b', 2)
        cache.clear()
        assert cache.get('a') is None
        assert cache.get('b') is None

    def test_simple_cache_expiry(self):
        from opentdx.utils.cache import SimpleCache
        cache = SimpleCache(ttl_seconds=0)  # immediate expiry
        cache.set('x', 1)
        assert cache.get('x') is None

    def test_module_level_caches(self):
        from opentdx.utils.cache import finance_cache
        assert finance_cache is not None


# ──────────────────────────────────────────────
# helper.py 额外覆盖
# ──────────────────────────────────────────────

class TestHelperDump:
    def test_dump(self, capsys):
        from opentdx.utils.helper import dump
        result = dump(b'\x01\x02\x03\x04')
        # dump prints to stdout and returns None
        captured = capsys.readouterr()
        assert result is None or isinstance(result, str)
        assert len(captured.out) > 0


# ──────────────────────────────────────────────
# baseStockClient _paginate 边界测试
# ──────────────────────────────────────────────

class TestPaginate:
    def test_paginate_empty(self):
        from opentdx.client.baseStockClient import _paginate
        result = _paginate(lambda s, c: [], 10, 30)
        assert isinstance(result, list)

    def test_paginate_count_zero(self):
        from opentdx.client.baseStockClient import _paginate
        result = _paginate(lambda s, c: [1, 2, 3], 5, 0)
        assert result == [1, 2, 3]

    def test_paginate_exact_page(self):
        from opentdx.client.baseStockClient import _paginate
        def fetch(s, c):
            return list(range(s, s + min(c, 5)))
        result = _paginate(fetch, 5, 10)
        assert len(result) == 10
        assert result == list(range(10))
