"""Crawler 子系统测试 — 使用预构建数据"""
import struct
import tempfile
import os

import pytest

from opentdx.crawler import HistoryFinancialCrawler, HistoryFinancialListCrawler
from opentdx.exceptions import ValidationException


class TestHistoryFinancialListCrawler:
    def test_parse(self):
        """测试财务文件列表解析"""
        crawler = HistoryFinancialListCrawler()
        content = "gpcw20241231.zip,abc123,1000\ngpcw20250331.zip,def456,2000\n"
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp_path = f.name

        try:
            with open(tmp_path, "rb") as f:
                result = crawler.parse(f)
            assert len(result) == 2
            assert result[0]["filename"] == "gpcw20241231.zip"
            assert result[0]["filesize"] == 1000
            assert result[1]["filename"] == "gpcw20250331.zip"
            assert result[1]["hash"] == "def456"
        finally:
            os.unlink(tmp_path)

    def test_no_content_bytes(self):
        crawler = HistoryFinancialListCrawler()
        with pytest.raises(ValidationException):
            crawler.get_content()


class TestHistoryFinancialCrawler:
    def test_parse_dat_file(self):
        """测试 .dat 财务数据解析"""
        header_fmt = "<1hI1H3L"
        stock_items = [
            (b"000001", b"S", 64),   # code, market_flag, foa
            (b"000002", b"S", 80),
        ]

        # Build header: (unknown, report_date, max_count, ..., ..., report_size)
        report_size = 8  # 2 floats
        header = struct.pack(header_fmt, 1, 20251231, len(stock_items), 0, report_size, 0)

        # Build stock items and data
        stock_data = []
        for code, mkt_flag, foa in stock_items:
            stock_data.append(struct.pack("<6s1c1L", code, mkt_flag, foa))

        # Position data: float fields per stock
        pos1 = len(header) + len(stock_items) * struct.calcsize("<6s1c1L")
        pos2 = pos1 + struct.calcsize("<2f")
        stock_data[0] = struct.pack("<6s1c1L", b"000001", b"S", pos1)
        stock_data[1] = struct.pack("<6s1c1L", b"000002", b"S", pos2)

        with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as f:
            f.write(header)
            f.write(b"".join(stock_data))
            f.write(struct.pack("<2f", 100.5, 200.3))  # stock 1 financials
            f.write(struct.pack("<2f", 300.1, 400.7))  # stock 2 financials
            tmp_path = f.name

        try:
            crawler = HistoryFinancialCrawler()
            with open(tmp_path, "rb") as f:
                result = crawler.parse(download_file=f)
            assert len(result) == 2
            assert result[0][0] == "000001"
            assert result[0][1] == 20251231
            assert result[1][0] == "000002"

            df = crawler.to_df(result)
            assert df is not None
            assert len(df) == 2
        finally:
            os.unlink(tmp_path)

    def test_to_df_empty(self):
        crawler = HistoryFinancialCrawler()
        assert crawler.to_df(None) is None
        assert crawler.to_df([]) is None

    def test_no_content_bytes(self):
        crawler = HistoryFinancialCrawler()
        with pytest.raises(ValidationException):
            crawler.get_content(filename="test.zip")
