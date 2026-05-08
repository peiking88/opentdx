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
        assert result is not None


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

    def test_get_list(self, eqc):
        result = eqc.get_list(start=0, count=5)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_quotes_list(self, eqc):
        result = eqc.get_quotes_list(EX_MARKET.US_STOCK)
        assert isinstance(result, list)

    def test_get_quotes_single(self, eqc):
        result = eqc.get_quotes_single(EX_MARKET.US_STOCK, 'TSLA')
        assert result is not None

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

    def test_get_history_transaction(self, eqc):
        result = eqc.get_history_transaction(EX_MARKET.US_STOCK, 'TSLA', date(2026, 4, 10))
        assert isinstance(result, list)

    def test_get_history_instrument_bars_range(self, eqc):
        result = eqc.get_history_instrument_bars_range(EX_MARKET.US_STOCK, 'TSLA', 20260401, 20260501)
        # 服务器可能不支持，返回 None 或 list
        if result is not None:
            assert isinstance(result, list)
            if len(result) > 0:
                assert "open" in result[0]

    def test_get_instrument_info(self, eqc):
        result = eqc.get_instrument_info(0, 10)
        # 服务器可能不支持
        if result is not None:
            assert isinstance(result, list)
            if len(result) > 0:
                assert "code" in result[0]

    def test_get_traffic_stats(self, eqc):
        result = eqc.get_traffic_stats()
        assert isinstance(result, dict)
        assert "send_pkg_num" in result
