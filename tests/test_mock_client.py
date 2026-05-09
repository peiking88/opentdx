"""
Mock 客户端测试 — 通过 mock call() 测试 client 方法链路，无需真实服务器。

覆盖因网络原因无法稳定运行的场景：错误路径、边界条件、异常处理。
"""
from datetime import date, datetime, time
from unittest.mock import patch

import pandas as pd
import pytest

from opentdx.const import MARKET, EX_MARKET, PERIOD, ADJUST, CATEGORY
from opentdx.exceptions import ValidationException
from opentdx.client.quotationClient import QuotationClient
from opentdx.client.exQuotationClient import exQuotationClient
from opentdx.tdxClient import TdxClient


# ──────────────────────────────────────────────
# QuotationClient Mock 测试
# ──────────────────────────────────────────────

class TestQuotationClientMock:
    """A股行情 — mock call() 测试"""

    def test_get_count_mock(self):
        client = QuotationClient()
        client.connected = True
        client.call = lambda p: 2847
        assert client.get_count(MARKET.SZ) == 2847

    def test_get_list_mock(self):
        client = QuotationClient()
        client.connected = True
        mock_data = [
            {'code': '000001', 'name': '平安银行', 'vol': 1000, 'pre_close': 12.5},
            {'code': '600000', 'name': '浦发银行', 'vol': 2000, 'pre_close': 8.5},
        ]
        client.call = lambda p: mock_data
        result = client.get_list(MARKET.SZ, 0, 2)
        assert len(result) == 2
        assert result[0]['code'] == '000001'

    def test_get_kline_mock(self):
        client = QuotationClient()
        client.connected = True
        mock_bar = {
            'datetime': datetime(2026, 5, 8, 15, 0),
            'open': 1137, 'high': 1142, 'low': 1130, 'close': 1130,
            'vol': 614950, 'amount': 575654656.0, 'turnover': 0.5,
        }
        client.call = lambda p: [mock_bar]
        result = client.get_kline(MARKET.SH, '000001', PERIOD.DAILY, count=1)
        assert len(result) == 1
        # get_kline 会将价格除以 1000
        assert 1.0 < result[0]['close'] < 2.0

    def test_get_quotes_mock(self):
        client = QuotationClient()
        client.connected = True
        mock_quote = {
            'market': MARKET.SZ, 'code': '000001',
            'close': 1250, 'open': 1230, 'high': 1280, 'low': 1220, 'pre_close': 1240,
            'vol': 500000, 'amount': 6000000.0, 'neg_price': 0, 'open_amount': 1,
            'rise_speed': 5, 'short_turnover': 5, 'opening_rush': 0,
            'vol_rise_speed': 1.5, 'depth': 50,
            'handicap': {
                'bid': [{'price': 1250, 'vol': 100}],
                'ask': [{'price': 1260, 'vol': 200}],
            },
        }
        client.call = lambda p: [mock_quote]
        result = client.get_quotes([(MARKET.SZ, '000001')])
        assert len(result) == 1
        assert result[0]['code'] == '000001'
        # _adjust_quotes_list 把价格除以 100: 1250→12.5
        assert 12.0 < result[0]['close'] < 13.0

    def test_get_index_info_mock(self):
        client = QuotationClient()
        client.connected = True
        # get_index_info 内部对每只股票调用 self.call(IndexInfo)，返回单个 dict（非列表）
        client.call = lambda p: {
            'market': MARKET.SH, 'code': '999999',
            'open': 330000, 'high': 335000, 'low': 328000,
            'close': 332000, 'pre_close': 330000, 'diff': 2000,
            'vol': 50000000, 'amount': 15000000000.0,
            'up_count': 800, 'down_count': 500, 'active': 100,
        }
        result = client.get_index_info([(MARKET.SH, '999999')])
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['code'] == '999999'
        # 价格被除以 100: 332000/100 = 3320.0
        assert 3000 < result[0]['close'] < 3500

    def test_get_company_info_mock(self):
        client = QuotationClient()
        client.connected = True
        call_count = [0]
        def mock_call(p):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{'name': '公司概况', 'filename': '000001_0.txt', 'start': 0, 'length': 500}]
            elif call_count[0] == 2:
                return {'content': '公司概况内容HTML...'}
            elif call_count[0] == 3:
                return []  # XDXR empty
            else:
                return None  # Finance
        client.call = mock_call
        result = client.get_company_info(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_tick_chart_mock(self):
        client = QuotationClient()
        client.connected = True
        client.call = lambda p: [{'price': 12.5, 'avg': 12.48, 'vol': 100}]
        result = client.get_tick_chart(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert result[0]['price'] > 0

    def test_get_transaction_mock(self):
        client = QuotationClient()
        client.connected = True
        client.call = lambda p: [
            {'time': time(9, 30), 'price': 1250, 'vol': 100, 'num': 5, 'buyorsell': 0},
        ]
        result = client.get_transaction(MARKET.SZ, '000001')
        # 价格被除以 100
        assert isinstance(result, list)

    def test_get_chart_sampling_mock(self):
        client = QuotationClient()
        client.connected = True
        points = [100.0 + i * 0.1 for i in range(20)]
        client.call = lambda p: points
        result = client.get_chart_sampling(MARKET.SZ, '000001')
        assert len(result) == 20


# ──────────────────────────────────────────────
# exQuotationClient Mock 测试
# ──────────────────────────────────────────────

class TestExQuotationClientMock:
    """扩展行情 — mock call() 测试"""

    def test_get_count_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: 15000
        assert client.get_count() == 15000

    def test_get_category_list_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: [{'market': 74, 'name': 'US_STOCK', 'code': 'US', 'abbr': 'US'}]
        result = client.get_category_list()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_list_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: [{'code': 'TSLA', 'name': 'Tesla Inc', 'market': 74}]
        result = client.get_list(0, 1)
        assert len(result) == 1
        assert result[0]['code'] == 'TSLA'

    def test_get_quotes_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: [{'market': 74, 'code': 'TSLA', 'close': 252.0}]
        result = client.get_quotes(EX_MARKET.US_STOCK, 'TSLA')
        assert len(result) == 1
        assert result[0]['close'] == 252.0

    def test_get_kline_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: [{'datetime': datetime(2026, 5, 8), 'open': 250.0, 'close': 252.0}]
        result = client.get_kline(EX_MARKET.US_STOCK, 'TSLA', PERIOD.DAILY, count=1)
        assert len(result) == 1
        assert result[0]['close'] == 252.0

    def test_get_tick_chart_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: [{'price': 100.5, 'avg': 100.3, 'vol': 5000}]
        result = client.get_tick_chart(EX_MARKET.HK_MAIN_BOARD, '09988')
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_chart_sampling_mock(self):
        client = exQuotationClient()
        client.connected = True
        points = [100.0 + i for i in range(10)]
        client.call = lambda p: points
        result = client.get_chart_sampling(EX_MARKET.HK_MAIN_BOARD, '09988')
        assert result == points

    def test_get_history_transaction_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: [{'time': time(9, 30), 'price': 250.0, 'vol': 100, 'action': 'BUY'}]
        result = client.get_history_transaction(EX_MARKET.US_STOCK, 'TSLA', date(2026, 5, 8))
        assert isinstance(result, list)

    def test_server_info_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: {'delay': 15, 'info': 'test'}
        result = client.server_info()
        assert result is not None
        assert result['delay'] == 15

    def test_login_mock(self):
        client = exQuotationClient()
        client.connected = True
        client.call = lambda p: True
        result = client.login()
        assert result is True


# ──────────────────────────────────────────────
# TdxClient 门面 Mock 测试
# ──────────────────────────────────────────────

class TestTdxClientMock:
    """TdxClient — mock call() 测试"""

    def test_stock_count_mock(self):
        client = TdxClient()
        client.quotation_client.connected = True
        client.quotation_client.call = lambda p: 2847
        assert client.stock_count(MARKET.SZ) == 2847

    def test_goods_count_mock(self):
        client = TdxClient()
        client.ex_quotation_client.connected = True
        client.ex_quotation_client.call = lambda p: 5000
        assert client.goods_count() == 5000

    def test_stock_k_data_mock(self):
        client = TdxClient()
        client.quotation_client.connected = True
        # stock_k_data 内部分页循环（8000/800=10次），首次返回2条后第二次返回空
        call_count = [0]
        def mock_kline(market, code, period, start, count, times=1, adjust=None):
            call_count[0] += 1
            if call_count[0] == 1:
                return [
                    {'datetime': datetime(2026, 5, 4, 15, 0), 'open': 1137, 'close': 1130, 'high': 1142, 'low': 1130, 'vol': 614950, 'amount': 575654656.0},
                    {'datetime': datetime(2026, 5, 5, 15, 0), 'open': 1130, 'close': 1135, 'high': 1140, 'low': 1125, 'vol': 500000, 'amount': 500000000.0},
                ]
            return []
        client.quotation_client.get_kline = mock_kline
        result = client.stock_k_data('000001', '2026-05-01', '2026-05-10')
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_get_traffic_stats_mock(self):
        client = TdxClient()
        client.quotation_client.connected = True
        client.ex_quotation_client.connected = True
        result = client.get_traffic_stats()
        assert 'quotation' in result
        assert 'ex_quotation' in result

    def test_stock_xdxr_mock(self):
        client = TdxClient()
        client.quotation_client.connected = True
        from datetime import datetime
        client.quotation_client.call = lambda p: [
            {'market': MARKET.SZ, 'code': b'000001',
             'date': datetime(2023, 6, 15, 15, 0), 'name': '除权除息',
             'fenhong': 0.285, 'peigujia': 0.0, 'songzhuangu': 0.0, 'peigu': 0.0}
        ]
        result = client.stock_xdxr(MARKET.SZ, '000001')
        assert len(result) == 1
        assert result[0]['name'] == '除权除息'
        assert result[0]['fenhong'] == 0.285

    def test_stock_finance_mock(self):
        client = TdxClient()
        client.quotation_client.connected = True
        client.quotation_client.call = lambda p: {'liutongguben': 1940591.875, 'code': '000001'}
        result = client.stock_finance(MARKET.SZ, '000001')
        assert isinstance(result, dict)
        assert result['code'] == '000001'

    def test_context_manager_mock(self):
        """验证 TdxClient 门面方法被转发到正确的内部客户端"""
        client = TdxClient()
        client.quotation_client.connected = True
        client.ex_quotation_client.connected = True

        # stock 方法 → quotation_client
        client.quotation_client.call = lambda p: [{'code': '000001'}]
        assert len(client.stock_list(MARKET.SZ)) == 1

        # goods 方法 → ex_quotation_client
        client.ex_quotation_client.call = lambda p: [{'code': 'TSLA'}]
        assert len(client.goods_list()) == 1


# ──────────────────────────────────────────────
# 错误路径和边界条件
# ──────────────────────────────────────────────

class TestErrorPaths:
    """无服务器错误路径覆盖"""

    def test_disconnected_returns_none(self):
        client = QuotationClient()
        client.connected = False
        client.raise_exception = False
        result = client.get_count(MARKET.SZ)
        assert result is None

    def test_raise_exception_on_disconnect(self):
        client = QuotationClient()
        client.connected = False
        client.raise_exception = True
        try:
            client.get_count(MARKET.SZ)
            assert False, "Should have raised"
        except Exception:
            pass

    def test_sp_mode_not_enabled(self):
        from opentdx.client.macQuotationClient import macQuotationClient
        client = macQuotationClient()
        client._sp_mode_enabled = False
        from opentdx.const import BOARD_TYPE
        with pytest.raises(ValidationException, match='sp'):
            client.get_board_count(BOARD_TYPE.HY)

    def test_empty_kline(self):
        client = QuotationClient()
        client.connected = True
        client.call = lambda p: []
        result = client.get_kline(MARKET.SZ, '000001', PERIOD.DAILY, count=10)
        assert result == []

    def test_none_quotes(self):
        client = QuotationClient()
        client.connected = True
        client.raise_exception = False
        client.call = lambda p: None
        # get_quotes wraps with _normalize_code_list when code is None -> list
        result = client.get_quotes([(MARKET.SZ, '000001')])
        assert result is None

    def test_get_unusual_empty(self):
        client = QuotationClient()
        client.connected = True
        client.call = lambda p: []
        result = client.get_unusual(MARKET.SZ, count=10)
        assert result == []

    def test_get_vol_profile_none(self):
        client = QuotationClient()
        client.connected = True
        client.raise_exception = False
        client.call = lambda p: None
        result = client.get_vol_profile(MARKET.SZ, '000001')
        assert result is None
