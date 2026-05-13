"""工具函数测试"""
import struct
import pytest

from opentdx.exceptions import ValidationException
from opentdx.utils.helper import (
    get_price, get_datetime, get_time, get_security_type,
    get_security_coefficient, time_frame, index_bytes,
)
from opentdx.utils.helper import get_volume


class TestGetPrice:
    def test_simple_positive(self):
        # 简单正数编码: 0x01 → 没有 sign 位或扩展位
        data = bytearray([0x01])
        price, pos = get_price(data, 0)
        assert pos == 1
        assert price > 0

    def test_simple_zero(self):
        data = bytearray([0x00])
        price, pos = get_price(data, 0)
        assert price == 0

    def test_sign_negative(self):
        # 位6 (0x40) 设置表示负数
        data = bytearray([0x41])
        price, pos = get_price(data, 0)
        assert price == -1

    def test_multi_byte(self):
        # 位7 (0x80) 设置表示更多字节; 0x80的data=0, 0x01左移6位=64
        data = bytearray([0x80, 0x01])
        price, pos = get_price(data, 0)
        assert price == 64

    def test_boundary_eob_single_byte(self):
        """单字节数据，pos 超出范围应抛 ValidationException"""
        data = bytearray([0x41])
        with pytest.raises(ValidationException, match='越界'):
            get_price(data, 1)

    def test_boundary_eob_multibyte(self):
        """多字节编码中途越界应抛 ValidationException"""
        data = bytearray([0x80])  # 0x80 表示还有后续字节但数据已结束
        with pytest.raises(ValidationException, match='越界'):
            get_price(data, 0)


class TestGetDatetime:
    def test_daily_kline_date(self):
        # 日K线: 分类4, 原始uint32日期
        buffer = struct.pack("<I", 20260506)
        year, month, day, hour, minute, pos = get_datetime(4, buffer, 0)
        assert year == 2026
        assert month == 5
        assert day == 6
        assert hour == 15
        assert minute == 0

    def test_minute_kline_date(self):
        # 分钟K线: 分类0, 压缩 uint16 (year<<11 | month*100+day), minutes
        # 2026-05-06 → (2026-2004)<<11 | (5*100+6) = 45056 | 506 = 45562
        zip_day = (22 << 11) | (5 * 100 + 6)
        minutes = 570  # 9:30 = 570 minutes
        buffer = struct.pack("<HH", zip_day, minutes)
        year, month, day, hour, minute, pos = get_datetime(0, buffer, 0)
        assert year == 2026
        assert month == 5
        assert day == 6
        assert hour == 9
        assert minute == 30
        assert pos == 4

    def test_boundary_eob(self):
        """buffer 不足 4 字节应抛 ValidationException"""
        with pytest.raises(ValidationException, match='越界'):
            get_datetime(4, b'\x00\x00\x00', 0)


class TestGetTime:
    def test_basic(self):
        import struct
        buffer = struct.pack("<H", 570)  # 570分钟 = 9:30
        hour, minute, pos = get_time(buffer, 0)
        assert hour == 9
        assert minute == 30
        assert pos == 2

    def test_boundary_eob(self):
        """buffer 不足 2 字节应抛 ValidationException"""
        with pytest.raises(ValidationException, match='越界'):
            get_time(b'\x00', 0)


class TestGetSecurityType:
    def test_sz_a_stock(self):
        assert get_security_type(0, "000001") == "SZ_A_STOCK"
        assert get_security_type("SZ", "300750") == "SZ_A_STOCK"

    def test_sz_index(self):
        assert get_security_type(0, "399001") == "SZ_INDEX"

    def test_sh_a_stock(self):
        assert get_security_type(1, "600000") == "SH_A_STOCK"
        assert get_security_type("SH", "688001") == "SH_A_STOCK"

    def test_sh_index(self):
        assert get_security_type(1, "999999") == "SH_INDEX"

    def test_unknown(self):
        with pytest.raises(NotImplementedError):
            get_security_type(99, "123456")


class TestTimeFrame:
    def test_returns_bool(self):
        assert isinstance(time_frame(), bool)

    def test_during_trading_hours(self):
        """交易时段内（上午 10:00）应返回 True"""
        from datetime import datetime
        t = datetime(2026, 5, 13, 10, 0, 0)
        assert time_frame(t) is True

    def test_outside_trading_hours(self):
        """非交易时段（晚上 20:00）应返回 False"""
        from datetime import datetime
        t = datetime(2026, 5, 13, 20, 0, 0)
        assert time_frame(t) is False


class TestGetSecurityCoefficient:
    def test_a_stock(self):
        coef = get_security_coefficient(0, "000001")
        assert coef == 0.01

    def test_index(self):
        coef = get_security_coefficient(1, "999999")
        assert coef == 0.01

    def test_b_stock(self):
        """B 股系数应为 0.001"""
        coef = get_security_coefficient(1, "900001")
        assert coef == 0.001

    def test_bond(self):
        """债券系数应为 0.0001"""
        coef = get_security_coefficient(1, "010001")
        assert coef == 0.0001


class TestIndexBytes:
    def test_basic(self):
        assert index_bytes(bytearray([5, 10, 15]), 1) == 10


class TestGetVolume:
    def test_returns_number(self):
        # get_volume(0): logpoint=0, all mantissa bytes=0 → result ≈ 0
        result = get_volume(0)
        assert isinstance(result, float)
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_non_zero(self):
        # 用典型的成交量值测试，验证结果为正浮点数
        result = get_volume(1000000)
        assert isinstance(result, float)
        assert result > 0

    def test_volume_max_uint32(self):
        # 边界值：最大 uint32 不应崩溃，返回有效浮点数
        result = get_volume(0xFFFFFFFF)
        assert isinstance(result, float)
        assert result > 0


class TestToDf:
    def test_list(self):
        from opentdx.utils.to_df import to_df
        import pandas as pd
        df = to_df([{"a": 1}, {"a": 2}])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_dict(self):
        from opentdx.utils.to_df import to_df
        import pandas as pd
        df = to_df({"a": 1})
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_none(self):
        from opentdx.utils.to_df import to_df
        import pandas as pd
        df = to_df(None)
        assert isinstance(df, pd.DataFrame)

    def test_dataframe_passthrough(self):
        from opentdx.utils.to_df import to_df
        import pandas as pd
        original = pd.DataFrame({"a": [1, 2]})
        df = to_df(original)
        assert df is original
