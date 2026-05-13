from datetime import date

from opentdx.const import (
    BLOCK_FILE_TYPE,
    CATEGORY,
    MARKET,
    PERIOD,
)


class TestQuotationClientLogin:
    """登录和心跳"""

    def test_connected(self, qc):
        assert qc.connected is True

    def test_login_show_info(self, qc):
        result = qc.login(show_info=True)
        assert result is True

    def test_get_text_file(self, qc):
        result = qc.get_text_file('gpcw2026.zip')
        assert isinstance(result, list)

    def test_heartbeat(self, qc):
        result = qc.doHeartBeat()
        assert isinstance(result, int), f"心跳应返回日期整数，实际类型: {type(result)}"
        assert result > 20000101, f"心跳日期应 > 20000101，实际: {result}"

    def test_download_file(self, qc):
        result = qc.download_file('gpcw2026.zip', filesize=100)
        if result is not None:
            assert isinstance(result, bytearray)

    def test_get_traffic_stats(self, qc):
        result = qc.get_traffic_stats()
        assert isinstance(result, dict)
        assert "send_pkg_num" in result


class TestQuotationClientStock:
    """A 股行情 API"""

    def test_get_count(self, qc):
        result = qc.get_count(MARKET.SZ)
        assert isinstance(result, int)
        assert result > 0

    def test_get_count_sh(self, qc):
        result = qc.get_count(MARKET.SH)
        assert isinstance(result, int)
        assert result > 0

    def test_get_list(self, qc):
        result = qc.get_list(MARKET.SZ, start=0, count=5)
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'code' in result[0] and 'name' in result[0]
        assert result[0]['pre_close'] > 0, f"pre_close 应>0: {result[0]['pre_close']}"
        assert result[0]['vol'] >= 0, f"vol 应>=0: {result[0]['vol']}"

    def test_get_kline(self, qc):
        result = qc.get_kline(MARKET.SH, '000001', PERIOD.DAILY, count=10)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['open'] > 0, f"开盘价应>0: {result[0]['open']}"
        assert result[0]['close'] > 0, f"收盘价应>0: {result[0]['close']}"
        assert 'datetime' in result[0]

    def test_get_quotes(self, qc):
        result = qc.get_quotes(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['code'] == '000001'
        assert result[0]['close'] > 0, f"现价应>0: {result[0]['close']}"

    def test_get_quotes_multi(self, qc):
        result = qc.get_quotes([(MARKET.SZ, '000001'), (MARKET.SH, '600000')])
        assert isinstance(result, list)
        assert len(result) >= 2
        for r in result:
            assert r['close'] > 0, f"close 应>0: {r['code']} close={r['close']}"
            assert r['high'] >= r['low'], f"high < low: {r['code']}"

    def test_get_stock_quotes_details(self, qc):
        result = qc.get_stock_quotes_details(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'handicap' in result[0]
        h = result[0]['handicap']
        assert len(h['bid']) >= 1, "缺少买盘档位"
        assert len(h['ask']) >= 1, "缺少卖盘档位"
        if h['bid'][0]['vol'] > 0 and h['ask'][0]['vol'] > 0:
            assert h['bid'][0]['price'] < h['ask'][0]['price'], \
                f"买一价应<卖一价: bid={h['bid'][0]['price']}, ask={h['ask'][0]['price']}"

    def test_get_stock_quotes_details_multi(self, qc):
        result = qc.get_stock_quotes_details([(MARKET.SZ, '000001'), (MARKET.SH, '600000')])
        assert isinstance(result, list)
        assert len(result) >= 2
        for r in result:
            assert 'handicap' in r
            assert r['close'] > 0

    def test_get_stock_top_board(self, qc):
        result = qc.get_stock_top_board(CATEGORY.A)
        assert isinstance(result, dict)
        assert len(result) > 0
        # 验证排名类别存在
        top_keys = list(result.keys())
        assert 'amplitude' in top_keys or '涨幅' in top_keys or 'rise' in top_keys, \
            f"缺少涨幅排名类别, keys={top_keys[:3]}"

    def test_get_stock_quotes_list(self, qc):
        result = qc.get_stock_quotes_list(CATEGORY.A, count=5)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_stock_quotes_list_sample(self, qc):
        result = qc.get_stock_quotes_list(CATEGORY.A, count=5)
        assert isinstance(result, list)
        assert len(result) == 5

    def test_get_tick_chart(self, qc):
        result = qc.get_tick_chart(MARKET.SH, '999999')
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['price'] >= 0, f"price 应>=0: {result[0]['price']}"
            assert result[0]['vol'] >= 0, f"vol 应>=0: {result[0]['vol']}"

    def test_get_transaction(self, qc):
        result = qc.get_transaction(MARKET.SZ, '000001')
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['price'] > 0, f"price 应>0: {result[0]['price']}"
            assert result[0]['vol'] > 0, f"vol 应>0: {result[0]['vol']}"
            assert result[0]['action'] in ('BUY', 'SELL', 'NEUTRAL'), \
                f"action 应为 BUY/SELL/NEUTRAL: {result[0]['action']}"

    def test_get_transaction_history(self, qc):
        result = qc.get_transaction(MARKET.SZ, '000001', date(2026, 4, 10))
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['price'] > 0
            assert result[0]['vol'] > 0

    def test_get_company_info(self, qc):
        result = qc.get_company_info(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) >= 3, f"F10 应至少含 3 个分类, 实际 {len(result)}"
        assert 'name' in result[0]
        assert len(result[0]['name']) > 0

    def test_get_auction(self, qc):
        result = qc.get_auction(MARKET.SZ, '300308')
        assert isinstance(result, list)
        if len(result) > 0:
            assert 'items' in result[0] or 'price' in result[0], \
                f"缺少 auction 关键字段: {list(result[0].keys())[:5]}"

    def test_get_unusual(self, qc):
        result = qc.get_unusual(MARKET.SZ)
        assert isinstance(result, list)
        if len(result) > 0:
            assert len(result[0]['desc']) > 0, "异动描述不应为空"
            assert result[0]['unusual_type'] >= 0

    def test_get_unusual_sample(self, qc):
        result = qc.get_unusual(MARKET.SZ, count=5)
        assert isinstance(result, list)
        if len(result) > 0:
            assert len(result[0]['desc']) > 0

    def test_get_index_info(self, qc):
        result = qc.get_index_info(MARKET.SH, '999999')
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['close'] > 0, f"指数收盘价应>0: {result[0]['close']}"
        assert result[0]['up_count'] + result[0]['down_count'] > 0, \
            "涨跌家数之和应>0"

    def test_get_index_info_multi(self, qc):
        result = qc.get_index_info([(MARKET.SH, '999999'), (MARKET.SZ, '399001')])
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_get_index_momentum(self, qc):
        result = qc.get_index_momentum(MARKET.SH, '999999')
        assert isinstance(result, list)
        if len(result) > 0 and isinstance(result[0], dict):
            assert 'momentum' in result[0] or 'up_count' in result[0], \
                f"缺少动量字段: {list(result[0].keys())[:5]}"

    def test_get_vol_profile(self, qc):
        result = qc.get_vol_profile(MARKET.SZ, '000001')
        if isinstance(result, list) and len(result) > 0:
            assert 'price' in result[0] or 'vol' in result[0], \
                f"缺少价量字段: {list(result[0].keys())[:5]}"

    def test_get_chart_sampling(self, qc):
        result = qc.get_chart_sampling(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) > 0, "分时采样点不应为空"
        assert isinstance(result[0], (int, float)), \
            f"采样值应为数值: {type(result[0])}"

    def test_get_block_file(self, qc):
        result = qc.get_block_file(BLOCK_FILE_TYPE.DEFAULT)
        assert result is not None
        assert isinstance(result, list)

    def test_get_history_orders(self, qc):
        result = qc.get_history_orders(MARKET.SZ, '000001', date(2026, 4, 10))
        assert isinstance(result, list)
        if len(result) > 0:
            assert result[0]['price'] > 0
            assert result[0]['vol'] > 0


class TestQuotationClientQuotesAdjustment:
    """quotes_adjustment 数据处理（内联数据）"""

    def test_quotes_adjustment(self, qc):
        data = [{
            'high': 100000, 'low': 99000, 'open': 99500,
            'close': 100000, 'pre_close': 99500, 'neg_price': -100,
            'open_amount': 100, 'rise_speed': 500,
            'handicap': {'bid': [{'price': 99500, 'vol': 100}], 'ask': [{'price': 100000, 'vol': 100}]},
            'market': None, 'code': None, 'vol': 0,
        }]
        result = qc.quotes_adjustment(data)
        assert len(result) == 1
        assert result[0]['close'] == 1000.0
        assert result[0]['rise_speed'] == '5.00%'
        assert result[0]['handicap']['bid'][0]['price'] == 995.0
        assert 'turnover' not in result[0]


class TestServerParsers:
    """服务端协议解析器 — 真实服务端往返测试"""

    def test_exchange_announcement(self, qc):
        """测试交易所公告解析器 (ExchangeAnnouncement, msg_id=0x2)"""
        from opentdx.parser.quotation.server import ExchangeAnnouncement
        result = qc.call(ExchangeAnnouncement())
        assert isinstance(result, dict)
        assert 'content' in result
        assert isinstance(result['content'], str)
        assert len(result['content']) > 0, "公告内容不应为空"

    def test_heartbeat(self, qc):
        """测试心跳包解析器 (HeartBeat, msg_id=0x4)"""
        from opentdx.parser.quotation.server import HeartBeat
        result = qc.call(HeartBeat())
        assert isinstance(result, int)
        assert result > 20000101  # 合理日期范围

    def test_announcement(self, qc):
        """测试服务商公告解析器 (Announcement, msg_id=0xa)"""
        from opentdx.parser.quotation.server import Announcement
        result = qc.call(Announcement())
        assert result is None or isinstance(result, dict)
        if result is not None:
            assert 'title' in result
            assert len(result['title']) > 0, "公告标题不应为空"

    def test_upgrade_tip(self, qc):
        """测试升级提示解析器 (UpgradeTip, msg_id=0xfdb)"""
        from opentdx.parser.quotation.server import UpgradeTip
        result = qc.call(UpgradeTip())
        assert isinstance(result, dict)
        assert 'tips' in result
        assert isinstance(result['tips'], str)
        if result['had'] == 1:
            assert isinstance(result['tips'], str)

    def test_login_info(self, qc):
        """测试登录信息解析器 (Login, msg_id=0xd) — 连接时已调用"""
        from opentdx.parser.quotation.server import Login
        result = qc.call(Login())
        assert isinstance(result, dict)
        assert 'server_name' in result
        assert len(result['server_name']) > 0, "服务器名称不应为空"

    def test_server_info(self, qc):
        """测试服务器信息解析器 (Info, msg_id=0x15)"""
        from opentdx.parser.quotation.server import Info
        result = qc.call(Info())
        assert isinstance(result, dict)
        assert 'delay' in result
        assert isinstance(result['delay'], int)


class TestQuotationClientFieldValidation:
    """验证真实数据的字段完整性和一致性"""

    def test_stock_list_fields(self, qc):
        """验证 stock_list 返回字段完整性"""
        result = qc.get_list(MARKET.SZ, start=0, count=10)
        assert len(result) > 0
        for item in result:
            assert isinstance(item['code'], str), f"code 应为 str: {item['code']}"
            assert isinstance(item['name'], str), f"name 应为 str"
            assert 'pre_close' in item, "缺少 pre_close 字段"
            assert 'vol' in item, "缺少 vol 字段"

    def test_kline_desc_order(self, qc):
        """验证 K 线时间倒序、价格非负"""
        result = qc.get_kline(MARKET.SH, '000001', PERIOD.DAILY, count=10)
        assert len(result) >= 2
        for bar in result:
            assert bar['open'] >= 0, f"open 应 >= 0: {bar['open']}"
            assert bar['close'] >= 0, f"close 应 >= 0"
            assert bar['high'] >= bar['low'], f"high({bar['high']}) < low({bar['low']})"
        # 按时间升序排列
        assert result[0]['datetime'] <= result[-1]['datetime'], "K 线未按时间升序"

    def test_quotes_handicap(self, qc):
        """验证五档行情结构"""
        result = qc.get_stock_quotes_details(MARKET.SZ, '000001')
        assert len(result) > 0
        h = result[0].get('handicap', {})
        assert 'bid' in h, "缺少 bid 档位"
        assert 'ask' in h, "缺少 ask 档位"

    def test_block_file_structure(self, qc):
        """验证板块文件返回结构"""
        from opentdx.const import BLOCK_FILE_TYPE
        result = qc.get_block_file(BLOCK_FILE_TYPE.DEFAULT)
        assert isinstance(result, list)
        if len(result) > 0:
            assert 'blockname' in result[0], "缺少 blockname 字段"
            assert 'code' in result[0], "缺少 code 字段"
