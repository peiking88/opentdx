"""AdjustmentFactorCrawler 测试"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from opentdx.const import MARKET, ADJUST
from opentdx.crawler.adjustment_factor_crawler import AdjustmentFactorCrawler, _parse_event_date


class TestAdjustmentFactorCrawler:
    def test_normalize_events_empty(self):
        crawler = AdjustmentFactorCrawler()
        result = crawler._normalize_events(None, MARKET.SZ, "000001")
        assert result == []

    def test_normalize_events_with_data(self):
        """测试事件标准化"""
        crawler = AdjustmentFactorCrawler()
        events = [
            {
                "market": MARKET.SZ,
                "code": b"000001\x00",
                "date": "2026-05-01",
                "name": "除权除息",
                "fenhong": 0.5,
                "peigujia": None,
                "songzhuangu": None,
                "peigu": None,
            }
        ]
        result = crawler._normalize_events(events, MARKET.SZ, "000001")
        assert len(result) == 1
        assert result[0]["code"] == "000001"
        assert result[0]["market"] == 0  # MARKET.SZ.value
        assert result[0]["fenhong"] == 0.5

    def test_fetch_without_client_raises(self):
        """测试未设置 client 时抛出异常"""
        crawler = AdjustmentFactorCrawler()
        with pytest.raises(RuntimeError, match="未设置 client"):
            crawler.fetch_adjustment_factors(MARKET.SZ, "000001")

    def test_fetch_safe_returns_empty_on_error(self):
        """测试安全获取在异常时返回空列表"""
        crawler = AdjustmentFactorCrawler()
        result = crawler.fetch_adjustment_factors_safe(MARKET.SZ, "000001")
        assert result == []

    def test_save_and_load_json(self):
        """测试 JSON 序列化和反序列化"""
        data = {
            "000001": [
                {"market": 0, "code": "000001", "date": "2026-05-01", "name": "除权除息", "fenhong": 0.5},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AdjustmentFactorCrawler(output_dir=tmpdir)
            filepath = crawler.save_to_json(data, market=MARKET.SZ, filename="test_xdxr.json")

            assert Path(filepath).is_file()

            loaded = crawler.load_from_json(filepath)
            assert "metadata" in loaded
            assert "factors" in loaded
            assert loaded["factors"]["000001"][0]["fenhong"] == 0.5

    def test_compute_qfq_empty(self):
        """测试空事件列表的 QFQ 计算"""
        result = AdjustmentFactorCrawler.compute_qfq([])
        assert result == []

    def test_compute_qfq_single_event(self):
        """测试单个除权除息事件的 QFQ 计算"""
        events = [
            {
                "market": 0,
                "code": "000001",
                "date": "2026-05-01",
                "name": "除权除息",
                "fenhong": 0.5,
                "peigujia": 5.0,
                "songzhuangu": 0.3,
                "peigu": 0.2,
            }
        ]
        result = AdjustmentFactorCrawler.compute_qfq(events)
        assert len(result) == 1
        assert "fenhong_num" in result[0]
        assert "peigu_num" in result[0]
        assert "denom_add" in result[0]
        assert "qfq_cumulative_factor" in result[0]
        assert result[0]["fenhong_num"] == 0.5
        assert result[0]["peigu_num"] == 0.2 * 5.0  # peigu * peigujia = 1.0
        assert result[0]["denom_add"] == 0.5  # songzhuangu + peigu = 0.3 + 0.2 = 0.5

    def test_compute_qfq_multiple_events(self):
        """测试多个除权除息事件的 QFQ 累积顺序（从最近到最早）"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-01",
                "name": "除权除息", "fenhong": 0.5,
                "peigujia": None, "songzhuangu": None, "peigu": None,
            },
            {
                "market": 0, "code": "000001", "date": "2026-01-15",
                "name": "除权除息", "fenhong": 0.3,
                "peigujia": None, "songzhuangu": None, "peigu": None,
            },
        ]
        result = AdjustmentFactorCrawler.compute_qfq(events)
        assert len(result) == 2
        # 结果按日期升序（从早到晚）
        assert result[0]["date"] == "2026-01-15"
        assert result[1]["date"] == "2026-05-01"

    def test_compute_hfq_empty(self):
        """测试空事件列表的 HFQ 计算"""
        result = AdjustmentFactorCrawler.compute_hfq([])
        assert result == []

    def test_compute_hfq_single_event(self):
        """测试单个除权除息事件的 HFQ 计算"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-01",
                "name": "除权除息",
                "fenhong": 0.5, "peigujia": 5.0,
                "songzhuangu": 0.3, "peigu": 0.2,
            }
        ]
        result = AdjustmentFactorCrawler.compute_hfq(events)
        assert len(result) == 1
        assert "hfq_numer_add" in result[0]
        assert "hfq_denom_sub" in result[0]
        assert "hfq_cumulative_factor" in result[0]
        assert result[0]["hfq_numer_add"] == 0.5  # songzhuangu + peigu = 0.3 + 0.2
        assert result[0]["hfq_denom_sub"] == 0.5 - 0.2 * 5.0  # fenhong - peigu * peigujia = 0.5 - 1.0 = -0.5

    def test_compute_hfq_multiple_events(self):
        """测试多个除权除息事件的 HFQ 累积顺序（从早到晚）"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-01",
                "name": "除权除息", "fenhong": 0.5,
                "peigujia": None, "songzhuangu": None, "peigu": None,
            },
            {
                "market": 0, "code": "000001", "date": "2026-01-15",
                "name": "除权除息", "fenhong": 0.3,
                "peigujia": None, "songzhuangu": None, "peigu": None,
            },
        ]
        result = AdjustmentFactorCrawler.compute_hfq(events)
        assert len(result) == 2
        # 结果按日期升序（从早到晚）
        assert result[0]["date"] == "2026-01-15"
        assert result[1]["date"] == "2026-05-01"

    def test_compute_full_factor_qfq(self):
        """测试完整前复权因子计算"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-08",
                "name": "除权除息",
                "fenhong": 0.5, "peigujia": None,
                "songzhuangu": 0.5, "peigu": None,
            },
        ]
        pre_close_prices = {"2026-05-08": 10.0}

        result = AdjustmentFactorCrawler.compute_full_factor(events, pre_close_prices, adjust=ADJUST.QFQ)
        assert len(result) == 1
        assert "factor" in result[0]
        # QFQ: (10 - 0.5 + 0) / (10 + 0.5 + 0) = 9.5 / 10.5
        expected = 9.5 / 10.5
        assert abs(result[0]["factor"] - expected) < 0.0001

    def test_compute_full_factor_hfq(self):
        """测试完整后复权因子计算"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-08",
                "name": "除权除息",
                "fenhong": 0.5, "peigujia": None,
                "songzhuangu": 0.5, "peigu": None,
            },
        ]
        pre_close_prices = {"2026-05-08": 10.0}

        result = AdjustmentFactorCrawler.compute_full_factor(events, pre_close_prices, adjust=ADJUST.HFQ)
        assert len(result) == 1
        # HFQ: (10 + 0.5 + 0) / (10 - 0.5 + 0) = 10.5 / 9.5
        expected = 10.5 / 9.5
        assert abs(result[0]["factor"] - expected) < 0.0001

    def test_compute_full_factor_with_peigu(self):
        """测试含配股的复权因子计算"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-08",
                "name": "除权除息",
                "fenhong": 0.3, "peigujia": 8.0,
                "songzhuangu": 0.0, "peigu": 0.3,
            },
        ]
        pre_close_prices = {"2026-05-08": 12.0}

        result = AdjustmentFactorCrawler.compute_full_factor(events, pre_close_prices, adjust=ADJUST.QFQ)
        assert len(result) == 1
        # QFQ: (12 - 0.3 + 8*0.3) / (12 + 0 + 0.3) = (12 - 0.3 + 2.4) / 12.3 = 14.1 / 12.3
        expected = (12.0 - 0.3 + 8.0 * 0.3) / (12.0 + 0.3)
        assert abs(result[0]["factor"] - expected) < 0.0001

    def test_no_client_initialization(self):
        """测试无 client 时构造函数正常工作"""
        crawler = AdjustmentFactorCrawler()
        assert crawler.client is None
        assert crawler.output_dir.exists()

    def test_batch_fetch_with_empty_codes(self):
        """测试批量下载空代码列表"""
        crawler = AdjustmentFactorCrawler()
        results = crawler.batch_fetch(markets=[], codes=[])
        assert results == {}

    def test_read_mock_xdxr(self):
        """测试 mock XDXR 数据流程"""
        # Mock client
        mock_client = MagicMock()
        mock_client.call.return_value = [
            {
                "market": MARKET.SZ,
                "code": b"000001\x00",
                "date": "2026-05-01",
                "name": "除权除息",
                "fenhong": 0.5,
                "peigujia": None,
                "songzhuangu": None,
                "peigu": None,
                "suogu": None,
                "xingquanjia": None,
                "fenshu": None,
                "panqianliutong": None,
                "qianzongguben": None,
                "panhouliutong": None,
                "houzongguben": None,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AdjustmentFactorCrawler(client=mock_client, output_dir=tmpdir)
            result = crawler.fetch_adjustment_factors(MARKET.SZ, "000001")
            assert len(result) == 1
            assert result[0]["code"] == "000001"
            assert result[0]["fenhong"] == 0.5

    def test_save_json_with_default_filename(self):
        """测试使用默认文件名的 JSON 保存"""
        data = {"000001": [{"market": 0, "code": "000001", "date": "2026-01-01", "name": "除权除息", "fenhong": 0.1}]}

        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = AdjustmentFactorCrawler(output_dir=tmpdir)
            filepath = crawler.save_to_json(data, market=MARKET.SZ)
            assert Path(filepath).is_file()
            assert "xdxr_0_" in filepath

            loaded = crawler.load_from_json(filepath)
            assert loaded["metadata"]["count"] == 1

    def test_non_category_one_events(self):
        """测试非 category=1 事件的处理"""
        events = [
            {
                "market": 0, "code": "000001", "date": "2026-05-01",
                "name": "送配股上市",
                "fenhong": None, "peigujia": None,
                "songzhuangu": None, "peigu": None,
                "panqianliutong": 1000000, "qianzongguben": 5000000,
                "panhouliutong": 1500000, "houzongguben": 6000000,
            }
        ]
        qfq_result = AdjustmentFactorCrawler.compute_qfq(events)
        assert qfq_result[0]["fenhong_num"] == 0.0
        assert qfq_result[0]["peigu_num"] == 0.0
        assert qfq_result[0]["denom_add"] == 0.0

        hfq_result = AdjustmentFactorCrawler.compute_hfq(events)
        assert hfq_result[0]["hfq_numer_add"] == 0.0
        assert hfq_result[0]["hfq_denom_sub"] == 0.0


class TestParseEventDate:
    """_parse_event_date 单元测试"""

    def test_datetime_object(self):
        from datetime import datetime
        dt = datetime(2026, 5, 8)
        y, m, d = _parse_event_date({"date": dt})
        assert (y, m, d) == (2026, 5, 8)

    def test_string_date(self):
        y, m, d = _parse_event_date({"date": "2026-05-08"})
        assert (y, m, d) == (2026, 5, 8)

    def test_fallback(self):
        y, m, d = _parse_event_date({})
        assert (y, m, d) == (2000, 1, 1)
