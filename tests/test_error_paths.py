"""
错误路径和边界条件测试 — 覆盖无需真实服务器的异常场景。
断连、空数据、异常抛出等难以用真实服务器触发的路径。
"""
from datetime import date, datetime, time

import pytest

from opentdx.const import MARKET, EX_MARKET, PERIOD
from opentdx.exceptions import ValidationException, TdxConnectionError, TdxFunctionCallError
from opentdx.client.quotationClient import QuotationClient
from opentdx.client.exQuotationClient import exQuotationClient


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
        with pytest.raises((TdxConnectionError, TdxFunctionCallError)):
            client.get_count(MARKET.SZ)

    def test_disconnect_then_call_returns_none(self):
        """disconnect() 后再调用 API，raise_exception=False 应返回 None"""
        client = QuotationClient()
        client.raise_exception = False
        client.disconnect()
        result = client.get_count(MARKET.SZ)
        assert result is None

    def test_disconnect_then_call_raises(self):
        """disconnect() 后再调用 API，raise_exception=True 应抛出异常"""
        client = QuotationClient()
        client.raise_exception = True
        client.disconnect()
        with pytest.raises((TdxConnectionError, TdxFunctionCallError)):
            client.get_count(MARKET.SZ)

    def test_ex_client_disconnect_then_call_returns_none(self):
        """扩展行情客户端 disconnect() 后 API 应返回 None"""
        client = exQuotationClient()
        client.raise_exception = False
        client.disconnect()
        result = client.get_count()
        assert result is None

    def test_call_parse_failure_raises(self):
        """mock send 返回有效数据但解析失败，raise_exception=True 应抛 TdxFunctionCallError"""
        client = QuotationClient()
        client.connected = True
        client.raise_exception = True
        client.send = lambda data: b'\x00' * 20
        with pytest.raises(TdxFunctionCallError):
            client.get_count(MARKET.SZ)

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
