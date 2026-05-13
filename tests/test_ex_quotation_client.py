from datetime import date

from opentdx.const import EX_MARKET, PERIOD


class TestExQuotationClientLogin:
    """登录和服务器信息"""

    def test_connected(self, eqc):
        assert eqc.connected is True

    def test_login_show_info(self, eqc):
        result = eqc.login(show_info=True)
        assert isinstance(result, bool)

    def test_server_info(self, eqc):
        result = eqc.server_info()
        assert isinstance(result, dict), "服务端信息应返回字典"
        assert 'name' in result, "缺少 name (服务器名称) 字段"
        assert len(result['name']) > 0, "服务器名称不应为空"
        assert 'version' in result, "缺少 version 字段"


class TestExQuotationClientData:
    """扩展行情 API"""

    def test_get_count(self, eqc):
        result = eqc.get_count()
        assert isinstance(result, int)
        assert result >= 0

    def test_get_category_list(self, eqc):
        result = eqc.get_category_list()
        assert isinstance(result, list)
        assert len(result) > 0
        assert len(result[0].get('name', result[0].get('abbr', ''))) > 0

    def test_get_list(self, eqc):
        result = eqc.get_list(start=0, count=5)
        assert isinstance(result, list)
        assert len(result) > 0
        assert len(result[0]['code']) > 0, "code 不应为空"

    def test_get_quotes_list(self, eqc):
        result = eqc.get_quotes_list(EX_MARKET.US_STOCK)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['close'] > 0, f"close 应>0: {result[0]['close']}"

    def test_get_quotes_single(self, eqc):
        result = eqc.get_quotes_single(EX_MARKET.US_STOCK, 'TSLA')
        assert result is not None
        assert result['close'] > 0

    def test_get_quotes(self, eqc):
        result = eqc.get_quotes(EX_MARKET.US_STOCK, 'TSLA')
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['code'] == 'TSLA'
        assert result[0]['close'] > 0

    def test_get_quotes_multi(self, eqc):
        result = eqc.get_quotes([(EX_MARKET.US_STOCK, 'TSLA'), (EX_MARKET.HK_MAIN_BOARD, '09988')])
        assert isinstance(result, list)
        assert len(result) >= 2
        codes = {r['code'] for r in result}
        assert 'TSLA' in codes
        assert '09988' in codes
        for r in result:
            assert r['close'] > 0, f"close 应>0: {r['code']}"

    def test_get_kline(self, eqc):
        result = eqc.get_kline(EX_MARKET.US_STOCK, 'TSLA', PERIOD.DAILY, count=5)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['open'] > 0
        assert result[0]['close'] > 0
        assert 'date_time' in result[0] or 'datetime' in result[0]

    def test_get_tick_chart(self, eqc):
        result = eqc.get_tick_chart(EX_MARKET.HK_MAIN_BOARD, '09988')
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['price'] > 0

    def test_get_chart_sampling(self, eqc):
        result = eqc.get_chart_sampling(EX_MARKET.HK_MAIN_BOARD, '09988')
        assert isinstance(result, list)
        assert len(result) > 0, "分时采样点不应为空"

    def test_get_history_transaction(self, eqc):
        result = eqc.get_history_transaction(EX_MARKET.US_STOCK, 'TSLA', date(2026, 4, 10))
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['price'] > 0
            assert result[0]['vol'] > 0

    def test_get_history_instrument_bars_range(self, eqc):
        result = eqc.get_history_instrument_bars_range(EX_MARKET.US_STOCK, 'TSLA', 20260401, 20260501)
        if result is not None:
            assert isinstance(result, list)
            if len(result) > 0:
                assert "open" in result[0]
                assert result[0]["open"] > 0

    def test_get_instrument_info(self, eqc):
        result = eqc.get_instrument_info(0, 10)
        if result is not None:
            assert isinstance(result, list)
            if len(result) > 0:
                assert "code" in result[0]
                assert len(result[0]["code"]) > 0
                assert len(result[0]["name"]) > 0

    def test_get_traffic_stats(self, eqc):
        result = eqc.get_traffic_stats()
        assert isinstance(result, dict)
        assert "send_pkg_num" in result


class TestExQuotationParserDetail:
    """扩展行情解析器 — 真实服务端往返细节验证"""

    def test_history_tick_chart(self, eqc):
        """测试分时数据解析器 (HistoryTickChart, msg_id=0x2404)"""
        from opentdx.parser.ex_quotation.history_tick_chart import HistoryTickChart
        from datetime import date
        result = eqc.call(HistoryTickChart(EX_MARKET.US_STOCK, 'TSLA', date(2026, 4, 10)))
        if result is not None:
            assert isinstance(result, list)
            if len(result) > 0:
                assert 'price' in result[0]
                assert result[0]['price'] > 0

    def test_instrument_info_detail(self, eqc):
        """测试品种信息解析器 (InstrumentInfo, msg_id=0x2401)"""
        from opentdx.parser.ex_quotation.instrument_info import InstrumentInfo
        result = eqc.call(InstrumentInfo(0, 20))
        if result is not None:
            assert isinstance(result, list)
            if len(result) > 0:
                assert isinstance(result[0]['code'], str)
                assert len(result[0]['code']) > 0
                assert isinstance(result[0]['name'], str)
                assert len(result[0]['name']) > 0

    def test_table_parser(self, eqc):
        """测试表格解析器 (Table, msg_id=0x2451)"""
        result = eqc.get_table()
        if result is not None:
            assert isinstance(result, tuple)
            assert len(result) == 3
