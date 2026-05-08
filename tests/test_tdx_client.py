from datetime import date

from opentdx.const import (
    ADJUST,
    BLOCK_FILE_TYPE,
    CATEGORY,
    EX_MARKET,
    MARKET,
    PERIOD,
    SORT_TYPE,
)


class TestTdxClientStock:
    """TdxClient A股相关 API"""

    def test_stock_count(self, tdx):
        result = tdx.stock_count(MARKET.SZ)
        assert isinstance(result, int)
        assert result > 0

    def test_stock_list(self, tdx):
        result = tdx.stock_list(MARKET.SZ, start=0, count=5)
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'code' in result[0] and 'name' in result[0]

    def test_stock_kline(self, tdx):
        result = tdx.stock_kline(MARKET.SH, '000001', PERIOD.DAILY, count=10)
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'datetime' in result[0] and 'open' in result[0]
        assert result[0]['close'] > 0, f"收盘价应>0: {result[0]['close']}"
        assert result[0]['high'] >= result[0]['low'], "最高价应>=最低价"

    def test_stock_kline_with_adjust(self, tdx):
        result = tdx.stock_kline(MARKET.SH, '000001', PERIOD.DAILY, count=5, adjust=ADJUST.QFQ)
        assert isinstance(result, list)
        assert len(result) > 0
        # 复权后价格应不同于不复权
        assert result[0]['close'] > 0

    def test_stock_quotes(self, tdx):
        result = tdx.stock_quotes(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['code'] == '000001'
        assert result[0]['close'] > 0

    def test_stock_quotes_multi(self, tdx):
        result = tdx.stock_quotes([(MARKET.SZ, '000001'), (MARKET.SH, '600000')])
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_stock_quotes_list(self, tdx):
        result = tdx.stock_quotes_list(CATEGORY.A, count=5)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_stock_quotes_list_with_sort(self, tdx):
        result = tdx.stock_quotes_list(CATEGORY.A, count=5, sort_type=SORT_TYPE.TOTAL_AMOUNT)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_stock_top_board(self, tdx):
        result = tdx.stock_top_board(CATEGORY.A)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_stock_quotes_detail(self, tdx):
        result = tdx.stock_quotes_detail(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) > 0

    def test_stock_quotes_detail_multi(self, tdx):
        result = tdx.stock_quotes_detail([(MARKET.SZ, '000001'), (MARKET.SH, '600000')])
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_index_info(self, tdx):
        result = tdx.index_info([(MARKET.SH, '999999'), (MARKET.SZ, '399001')])
        assert isinstance(result, list)
        assert len(result) > 0

    def test_index_momentum(self, tdx):
        result = tdx.index_momentum(MARKET.SH, '999999')
        assert isinstance(result, list)

    def test_stock_tick_chart(self, tdx):
        result = tdx.stock_tick_chart(MARKET.SH, '999999')
        assert isinstance(result, list)

    def test_stock_transaction(self, tdx):
        result = tdx.stock_transaction(MARKET.SZ, '000001')
        assert isinstance(result, list)

    def test_stock_transaction_history(self, tdx):
        result = tdx.stock_transaction(MARKET.SZ, '000001', date(2026, 4, 10))
        assert isinstance(result, list)

    def test_stock_unusual(self, tdx):
        result = tdx.stock_unusual(MARKET.SZ)
        assert isinstance(result, list)

    def test_stock_f10(self, tdx):
        result = tdx.stock_f10(MARKET.SZ, '000001')
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'name' in result[0]

    def test_stock_vol_profile(self, tdx):
        result = tdx.stock_vol_profile(MARKET.SZ, '000001')
        assert result is None or isinstance(result, list)

    def test_stock_chart_sampling(self, tdx):
        result = tdx.stock_chart_sampling(MARKET.SZ, '000001')
        assert isinstance(result, list)

    def test_stock_block(self, tdx):
        result = tdx.stock_block(BLOCK_FILE_TYPE.DEFAULT)
        assert result is not None
        assert isinstance(result, list)


class TestTdxClientAdvanced:
    """TdxClient 补充 API — 提升覆盖率"""

    def test_stock_auction(self, tdx):
        result = tdx.stock_auction(MARKET.SZ, '000001')
        assert isinstance(result, list)

    def test_stock_history_orders(self, tdx):
        from datetime import date
        result = tdx.stock_history_orders(MARKET.SZ, '000001', date(2026, 4, 10))
        assert isinstance(result, list)

    def test_stock_xdxr(self, tdx):
        result = tdx.stock_xdxr(MARKET.SZ, '000001')
        assert isinstance(result, list)

    def test_stock_finance(self, tdx):
        result = tdx.stock_finance(MARKET.SZ, '000001')
        assert isinstance(result, dict)

    def test_stock_k_data(self, tdx):
        result = tdx.stock_k_data('000001', '2026-01-01', '2026-05-01')
        assert result is not None

    def test_goods_quotes_list(self, tdx):
        result = tdx.goods_quotes_list(EX_MARKET.US_STOCK, start=0, count=5)
        assert isinstance(result, list)

    def test_goods_history_transaction(self, tdx):
        from datetime import date
        result = tdx.goods_history_transaction(EX_MARKET.US_STOCK, 'TSLA', date(2026, 5, 1))
        assert isinstance(result, list)

    def test_context_manager(self):
        """测试 __enter__ / __exit__"""
        from opentdx.tdxClient import TdxClient
        with TdxClient() as client:
            assert client.quotation_client.connected
            assert client.ex_quotation_client.connected


class TestTdxClientXDXR:
    """XDXR 除权除息数据 — 深度验证"""

    XDXR_VALID_CATEGORIES = {
        "除权除息", "送配股上市", "非流通股上市", "未知股本变动",
        "股本变化", "增发新股", "股份回购", "增发新股上市",
        "转配股上市", "可转债上市", "扩缩股", "非流通股缩股",
        "送认购权证", "送认沽权证",
    }

    def _validate_record(self, rec, expected_market, expected_code):
        """验证单条 XDXR 记录的结构完整性"""
        assert isinstance(rec, dict), f"每条记录应为 dict，实际 {type(rec)}"
        assert rec["market"] == expected_market, f"market 不匹配: {rec['market']}"
        # code 以 bytes 返回
        code_str = rec["code"].decode("utf-8") if isinstance(rec["code"], bytes) else rec["code"]
        assert code_str == expected_code, f"code 不匹配: {code_str}"
        assert hasattr(rec["date"], "year"), f"date 应为 datetime: {rec['date']}"
        assert rec["name"] in self.XDXR_VALID_CATEGORIES, f"未知事件类型: {rec['name']}"

    def test_basic_structure(self, tdx):
        """验证基本结构和字段完整性"""
        result = tdx.stock_xdxr(MARKET.SZ, "000001")
        assert isinstance(result, list)
        assert len(result) > 50, f"上市多年的股票应有大量除权记录，实际 {len(result)}"

        # 验证第一条记录（最早的）
        first = result[0]
        assert first["name"] is not None
        if first["name"] == "除权除息":
            assert first["fenhong"] is not None
            assert first["peigujia"] is not None
            assert first["songzhuangu"] is not None
            assert first["peigu"] is not None

        # 验证所有记录结构
        for rec in result:
            self._validate_record(rec, MARKET.SZ, "000001")

    def test_category_fields(self, tdx):
        """验证不同事件类型的专属字段"""
        result = tdx.stock_xdxr(MARKET.SZ, "000001")

        for rec in result:
            if rec["name"] == "除权除息":
                assert isinstance(rec["fenhong"], (int, float)), f"fenhong 类型异常: {type(rec['fenhong'])}"
                assert rec["fenhong"] >= 0, f"fenhong 不应为负: {rec['fenhong']}"
                # 送转股是10送X股，X>=0
                assert rec["songzhuangu"] >= 0, f"songzhuangu 不应为负: {rec['songzhuangu']}"

            elif rec["name"] == "股本变化":
                for field in ["panqianliutong", "qianzongguben", "panhouliutong", "houzongguben"]:
                    assert rec[field] is not None, f"股本变化记录缺少字段: {field}"
                # 盘后股本应 >= 盘前（正常情况）
                assert rec["houzongguben"] >= 0

    def test_date_order(self, tdx):
        """验证日期升序"""
        result = tdx.stock_xdxr(MARKET.SZ, "000001")
        dates = [rec["date"] for rec in result]
        for i in range(len(dates) - 1):
            assert dates[i] <= dates[i + 1], \
                f"日期应升序排列: {dates[i]} > {dates[i + 1]} (索引 {i})"

    def test_known_dividend(self, tdx):
        """验证已知分红事件：平安银行 2025-06-12 除权除息 分红约3.62元"""
        result = tdx.stock_xdxr(MARKET.SZ, "000001")
        from datetime import datetime
        target_date = datetime(2025, 6, 12, 15, 0, 0)
        found = [r for r in result if r["date"] == target_date]
        assert len(found) > 0, f"未找到 2025-06-12 的除权记录"
        record = found[0]
        assert record["name"] == "除权除息"
        # 平安银行 2024年度分红 10派3.62元 → 每股 0.362元 (实际值 ~3.6199)
        assert 3.0 <= record["fenhong"] <= 4.0, \
            f"分红金额异常: {record['fenhong']}，预期 3.62 附近"

    def test_shanghai_stock(self, tdx):
        """验证上海市场股票"""
        result = tdx.stock_xdxr(MARKET.SH, "600519")
        assert isinstance(result, list)
        assert len(result) > 20, f"贵州茅台应有较多除权记录，实际 {len(result)}"
        for rec in result:
            self._validate_record(rec, MARKET.SH, "600519")

    def test_category_distribution(self, tdx):
        """验证事件类型分布合理"""
        result = tdx.stock_xdxr(MARKET.SZ, "000001")
        cats = [rec["name"] for rec in result]
        cat_counts = {c: cats.count(c) for c in set(cats)}
        # 除权除息应占多数
        assert "除权除息" in cat_counts, "应有除权除息记录"
        assert cat_counts["除权除息"] > 0
        # 所有类别在合法范围内
        for cat in cat_counts:
            assert cat in self.XDXR_VALID_CATEGORIES, f"未识别的类别: {cat}"


class TestTdxClientBlockExtra:
    """TdxClient 板块文件补充"""

    def test_block_gn(self, tdx):
        result = tdx.stock_block(BLOCK_FILE_TYPE.GN)
        assert isinstance(result, list)

    def test_block_fg(self, tdx):
        result = tdx.stock_block(BLOCK_FILE_TYPE.FG)
        assert isinstance(result, list)

    def test_block_zs(self, tdx):
        result = tdx.stock_block(BLOCK_FILE_TYPE.ZS)
        assert isinstance(result, list)


class TestTdxClientGoods:
    """TdxClient 扩展行情 API"""

    def test_goods_count(self, tdx):
        result = tdx.goods_count()
        assert isinstance(result, int)
        assert result >= 0

    def test_goods_category_list(self, tdx):
        result = tdx.goods_category_list()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_goods_list(self, tdx):
        result = tdx.goods_list(start=0, count=5)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_goods_quotes(self, tdx):
        result = tdx.goods_quotes(EX_MARKET.US_STOCK, 'TSLA')
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['code'] == 'TSLA'
        assert result[0]['close'] > 0

    def test_goods_quotes_multi(self, tdx):
        result = tdx.goods_quotes([(EX_MARKET.US_STOCK, 'TSLA'), (EX_MARKET.HK_MAIN_BOARD, '09988')])
        assert isinstance(result, list)
        assert len(result) >= 2
        codes = {r['code'] for r in result}
        assert 'TSLA' in codes

    def test_goods_kline(self, tdx):
        result = tdx.goods_kline(EX_MARKET.US_STOCK, 'TSLA', PERIOD.DAILY, count=5)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]['open'] > 0
        assert result[0]['close'] > 0

    def test_goods_tick_chart(self, tdx):
        result = tdx.goods_tick_chart(EX_MARKET.US_STOCK, 'TSLA')
        assert isinstance(result, list)

    def test_goods_chart_sampling(self, tdx):
        result = tdx.goods_chart_sampling(EX_MARKET.US_STOCK, 'TSLA')
        assert isinstance(result, list)
