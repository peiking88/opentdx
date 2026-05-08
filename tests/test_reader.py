"""Reader 子系统测试 — 使用临时数据文件"""
import os
import struct
import tempfile
from pathlib import Path

import pytest

from opentdx.reader import (
    TdxDailyBarReader, TdxExHqDailyBarReader,
    TdxMinBarReader, TdxLCMinBarReader,
    TdxFileNotFoundException, TdxNotAssignVipdocPathException,
)
from opentdx.reader.base_reader import BaseReader


class TestBaseReader:
    def test_unpack_records(self):
        data = struct.pack("<2I", 100, 200)
        result = list(BaseReader.unpack_records("<I", data))
        assert len(result) == 2
        assert result[0] == (100,)
        assert result[1] == (200,)

    def test_parse_date(self):
        year, month, day = BaseReader._parse_date(0)
        assert year == 2004
        assert month == 0
        assert day == 0

        # 2026-05-08: (year-2004)=22, 22*2048 + 5*100 + 8 = 45056 + 500 + 8 = 45564
        year, month, day = BaseReader._parse_date(45564)
        assert year == 2026
        assert month == 5
        assert day == 8

    def test_parse_time(self):
        h, m = BaseReader._parse_time(570)
        assert h == 9
        assert m == 30

    def test_get_df_not_implemented(self):
        reader = BaseReader()
        with pytest.raises(NotImplementedError):
            reader.get_df("test")


class TestTdxDailyBarReader:
    def test_no_vipdoc_path(self):
        reader = TdxDailyBarReader()
        with pytest.raises(TdxNotAssignVipdocPathException):
            reader.generate_filename("000001", "sz")

    def test_file_not_found(self):
        reader = TdxDailyBarReader(vipdoc_path="/nonexistent")
        with pytest.raises(TdxFileNotFoundException):
            reader.get_df_by_file("/nonexistent/dayfile")

    def test_get_security_type(self):
        reader = TdxDailyBarReader()
        assert reader.get_security_type("sz000001.day") == "SZ_A_STOCK"
        assert reader.get_security_type("sz399001.day") == "SZ_INDEX"
        assert reader.get_security_type("sh600000.day") == "SH_A_STOCK"
        assert reader.get_security_type("sh999999.day") == "SH_INDEX"
        assert reader.get_security_type("sh688001.day") == "SH_A_STOCK"

    def test_unknown_security_type(self):
        reader = TdxDailyBarReader()
        with pytest.raises(NotImplementedError):
            reader.get_security_type("xx999999.day")

    def test_df_convert(self):
        row = (20260506, 1137, 1142, 1130, 1130, 575654656, 614950)
        result = TdxDailyBarReader._df_convert(row, [0.01, 0.01])
        assert result[0] == "2026-05-06"
        assert round(result[1], 2) == 11.37  # open * 0.01
        assert result[4] == 11.30  # close * 0.01
        assert result[5] == 575654656  # amount unchanged
        assert result[6] == 6149.5  # volume * 0.01

    def test_parse_and_df_with_temp_file(self):
        """用临时文件测试完整的日线解析流程"""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmpdir, "sz000001.day")

        records = []
        for i, d in enumerate([20260504, 20260505, 20260506]):
            row = struct.pack("<IIIIIfII",
                d, 1137 + i, 1142 + i, 1130 + i, 1130 + i,
                575654656.0, 614950, 0
            )
            records.append(row)

        with open(tmp_path, "wb") as f:
            f.write(b"".join(records))

        try:
            reader = TdxDailyBarReader()
            reader.SECURITY_COEFFICIENT["SZ_A_STOCK"] = [1.0, 1.0]
            raw = reader.parse_data_by_file(tmp_path)
            rows = list(raw)
            assert len(rows) == 3

            df = reader.get_df_by_file(tmp_path)
            assert len(df) == 3
        finally:
            os.unlink(tmp_path)
            os.rmdir(tmpdir)


class TestTdxExHqDailyBarReader:
    def test_parse_with_temp_file(self):
        """用临时文件测试扩展市场日线解析"""
        records = []
        for i in range(2):
            row = struct.pack("<IffffIIf",
                20260506,         # date
                250.0 + i,        # open
                255.0,            # high
                245.0,            # low
                252.0,            # close
                50000,            # amount
                1000000,          # volume
                251.5,            # settlement
            )
            records.append(row)

        with tempfile.NamedTemporaryFile(suffix=".day", delete=False) as f:
            f.write(b"".join(records))
            tmp_path = f.name

        try:
            reader = TdxExHqDailyBarReader()
            raw = reader.parse_data_by_file(tmp_path)
            rows = list(raw)
            assert len(rows) == 2

            df = reader.get_df(tmp_path)
            assert len(df) == 2
            assert "jiesuan" in df.columns
            assert "hk_stock_amount" in df.columns
        finally:
            os.unlink(tmp_path)


class TestTdxMinBarReader:
    def test_parse_with_temp_file(self):
        """用临时文件测试分钟线解析（整型版）"""
        # 每条32字节: <HHIIIIfII
        # date_zip, minutes, open, high, low, close, amount, volume, reserved
        zip_day = (22 << 11) | (5 * 100) | 6  # 2026-05-06
        records = []
        for m in [570, 575, 580]:  # 9:30, 9:35, 9:40
            row = struct.pack("<HHIIIIfII",
                zip_day, m,
                1137, 1142, 1130, 1135,
                500000,  # amount
                10000,   # volume
                0
            )
            records.append(row)

        with tempfile.NamedTemporaryFile(suffix=".lc5", delete=False) as f:
            f.write(b"".join(records))
            tmp_path = f.name

        try:
            reader = TdxMinBarReader()
            data = reader.parse_data_by_file(tmp_path)
            assert len(data) == 3
            assert "open" in data[0]
            assert data[0]["open"] == 11.37  # 1137 / 100
            assert data[0]["hour"] == 9
            assert data[0]["minute"] == 30

            df = reader.get_df(tmp_path)
            assert len(df) == 3
        finally:
            os.unlink(tmp_path)


class TestTdxLCMinBarReader:
    def test_parse_with_temp_file(self):
        """用临时文件测试分钟线解析（浮点版）"""
        zip_day = (22 << 11) | (5 * 100) | 6
        records = []
        for m in [570, 575]:
            row = struct.pack("<HHfffffII",
                zip_day, m,
                11.37, 11.42, 11.30, 11.35,
                500000.0,  # amount
                10000,     # volume
                0
            )
            records.append(row)

        with tempfile.NamedTemporaryFile(suffix=".lc5", delete=False) as f:
            f.write(b"".join(records))
            tmp_path = f.name

        try:
            reader = TdxLCMinBarReader()
            data = reader.parse_data_by_file(tmp_path)
            assert len(data) == 2
            assert round(data[0]["open"], 2) == 11.37
            assert round(data[0]["close"], 2) == 11.35

            df = reader.get_df(tmp_path)
            assert len(df) == 2
        finally:
            os.unlink(tmp_path)


class TestFileNotFound:
    def test_daily_bar_not_found(self):
        reader = TdxDailyBarReader()
        with pytest.raises(TdxFileNotFoundException):
            reader.get_df_by_file("/nonexistent/file.day")

    def test_min_bar_not_found(self):
        reader = TdxMinBarReader()
        with pytest.raises(TdxFileNotFoundException):
            reader.parse_data_by_file("/nonexistent/file.lc5")

    def test_lc_min_bar_not_found(self):
        reader = TdxLCMinBarReader()
        with pytest.raises(TdxFileNotFoundException):
            reader.parse_data_by_file("/nonexistent/file.lc5")
