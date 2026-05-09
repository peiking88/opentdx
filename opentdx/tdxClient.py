from datetime import date

from opentdx.client.exQuotationClient import exQuotationClient
from opentdx.client.quotationClient import QuotationClient
from opentdx.const import CATEGORY, EX_MARKET, MARKET, PERIOD, SORT_TYPE


# TdxClient → QuotationClient 方法映射: 对外名称 → 内部方法名
_STOCK_MAP = {
    "stock_count":          ("q_client", "get_count"),
    "stock_list":           ("q_client", "get_list"),
    "stock_vol_profile":    ("q_client", "get_vol_profile"),
    "stock_kline":          ("q_client", "get_kline"),
    "stock_tick_chart":     ("q_client", "get_tick_chart"),
    "stock_quotes_detail":  ("q_client", "get_stock_quotes_details"),
    "stock_top_board":      ("q_client", "get_stock_top_board"),
    "stock_quotes_list":    ("q_client", "get_stock_quotes_list"),
    "stock_quotes":         ("q_client", "get_quotes"),
    "stock_unusual":        ("q_client", "get_unusual"),
    "stock_auction":        ("q_client", "get_auction"),
    "stock_history_orders": ("q_client", "get_history_orders"),
    "stock_transaction":    ("q_client", "get_transaction"),
    "stock_chart_sampling": ("q_client", "get_chart_sampling"),
    "stock_f10":            ("q_client", "get_company_info"),
    "stock_block":          ("q_client", "get_block_file"),
    "index_momentum":       ("q_client", "get_index_momentum"),
    "index_info":           ("q_client", "get_index_info"),
    # 扩展市场
    "goods_count":                ("eq_client", "get_count"),
    "goods_category_list":        ("eq_client", "get_category_list"),
    "goods_list":                 ("eq_client", "get_list"),
    "goods_quotes_list":          ("eq_client", "get_quotes_list"),
    "goods_quotes":               ("eq_client", "get_quotes"),
    "goods_kline":                ("eq_client", "get_kline"),
    "goods_history_transaction":  ("eq_client", "get_history_transaction"),
    "goods_tick_chart":           ("eq_client", "get_tick_chart"),
    "goods_chart_sampling":       ("eq_client", "get_chart_sampling"),
}


class TdxClient:
    """统一行情入口，聚合 QuotationClient + exQuotationClient。

    通过 _STOCK_MAP 将对外方法名自动转发到内部客户端，避免手工维护 800 行代理代码。
    """

    def __init__(self):
        self.quotation_client = QuotationClient(True, True)
        self.ex_quotation_client = exQuotationClient(True, True)

    def __enter__(self):
        self.quotation_client.connect().login()
        self.ex_quotation_client.connect().login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.quotation_client.connected:
            self.quotation_client.disconnect()
        if self.ex_quotation_client.connected:
            self.ex_quotation_client.disconnect()

    def q_client(self):
        if not self.quotation_client.connected:
            self.quotation_client.connect().login()
        return self.quotation_client

    def eq_client(self):
        if not self.ex_quotation_client.connected:
            self.ex_quotation_client.connect().login()
        return self.ex_quotation_client

    def __getattr__(self, name):
        if name in _STOCK_MAP:
            client_attr, method = _STOCK_MAP[name]
            client = getattr(self, client_attr)()
            return getattr(client, method)
        raise AttributeError(
            f"'{type(self).__name__}' 无此方法: '{name}'。"
            f" 可用方法: {sorted(_STOCK_MAP.keys())}"
        )

    # ─── tdxpy 兼容方法（非简单转发） ───

    def stock_xdxr(self, market: MARKET, code: str) -> list[dict]:
        """获取除息除权信息（tdxpy兼容）"""
        import opentdx.parser.quotation as qp
        return self.q_client().call(qp.XDXR(market, code))

    def stock_finance(self, market: MARKET, code: str) -> dict:
        """获取财务信息（tdxpy兼容）"""
        import opentdx.parser.quotation as qp
        return self.q_client().call(qp.Finance(market, code))

    def stock_k_data(self, code: str, start_date: str, end_date: str):
        """获取K线DataFrame（tdxpy兼容），自动分页取约8000根日K"""
        import pandas as pd
        from opentdx.const import PERIOD

        market = MARKET.SH if code.startswith(('5', '6', '9')) else MARKET.SZ
        all_bars = []
        for start in range(0, 8000, 800):
            bars = self.q_client().get_kline(market, code, PERIOD.DAILY, start=start, count=800)
            if not bars:
                break
            all_bars.extend(bars)
            if len(bars) < 800:
                break

        if not all_bars:
            return pd.DataFrame()

        df = pd.DataFrame(all_bars)
        if 'datetime' in df.columns:
            df.index = pd.to_datetime(df['datetime'])
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        return df

    def get_traffic_stats(self) -> dict:
        """获取流量统计"""
        return {
            'quotation': self.quotation_client.get_traffic_stats() if self.quotation_client.connected else {},
            'ex_quotation': self.ex_quotation_client.get_traffic_stats() if self.ex_quotation_client.connected else {},
        }

    def stock_quotes_detail(self, code_list, code=None):
        return self.q_client().get_stock_quotes_details(code_list, code)

    def goods_quotes(self, code_list, code=None):
        return self.eq_client().get_quotes(code_list, code)


if __name__ == '__main__':
    import pandas as pd

    with TdxClient() as client:
        print(client.stock_count(MARKET.SZ))
        print(pd.DataFrame(client.stock_list(MARKET.SZ)))
        print(pd.DataFrame(client.index_momentum(MARKET.SZ, '399001')))
        print(pd.DataFrame(client.index_momentum(MARKET.SH, '999999')))
        print(pd.DataFrame(client.index_info([(MARKET.SZ, '399001'), (MARKET.SH, '999999')])))
        print(pd.DataFrame(client.stock_kline(MARKET.SH, '999999', PERIOD.DAILY)))
        print(pd.DataFrame(client.stock_kline(MARKET.SH, '999999', PERIOD.MINS, times=10)))
        print(pd.DataFrame(client.stock_tick_chart(MARKET.SH, '999999')))
        print(pd.DataFrame(client.stock_tick_chart(MARKET.SZ, '000001')))
        print(pd.DataFrame(client.stock_tick_chart(MARKET.SZ, '000001', date(2026, 3, 16))))
        print(pd.DataFrame(client.stock_quotes_detail(MARKET.SZ, '000001')))
        print(pd.DataFrame(client.stock_top_board()))
        print(pd.DataFrame(client.stock_quotes_list(CATEGORY.A, count=0, sortType=SORT_TYPE.TOTAL_AMOUNT)))
        print(pd.DataFrame(client.stock_quotes(MARKET.SZ, '000001')))
        print(pd.DataFrame(client.stock_unusual(MARKET.SZ)))
        print(pd.DataFrame(client.stock_auction(MARKET.SZ, '300308')))
        print(pd.DataFrame(client.stock_history_orders(MARKET.SZ, '000001', date(2026, 3, 16))))
        print(pd.DataFrame(client.stock_transaction(MARKET.SZ, '000001')))
        print(pd.DataFrame(client.stock_transaction(MARKET.SZ, '000001', date(2026, 3, 16))))
        print(pd.DataFrame(client.stock_chart_sampling(MARKET.SZ, '000001')))
        print(pd.DataFrame(client.stock_f10(MARKET.SZ, '000001')))

        print(client.goods_count())
        print(pd.DataFrame(client.goods_category_list()))
        print(pd.DataFrame(client.goods_list()))
        print(pd.DataFrame(client.goods_quotes_list(EX_MARKET.US_STOCK, sortType=SORT_TYPE.TOTAL_AMOUNT)))
        print(pd.DataFrame([client.goods_quotes(EX_MARKET.US_STOCK, 'TSLA')]))
        print(pd.DataFrame(client.goods_quotes([(EX_MARKET.US_STOCK, 'TSLA'), (EX_MARKET.HK_MAIN_BOARD, '09988')])))
        print(pd.DataFrame(client.goods_kline(EX_MARKET.US_STOCK, 'TSLA', PERIOD.DAILY)))
        print(pd.DataFrame(client.goods_history_transaction(EX_MARKET.US_STOCK, 'TSLA', date(2026, 3, 3))))
        print(pd.DataFrame(client.goods_tick_chart(EX_MARKET.US_STOCK, 'TSLA')))
        print(pd.DataFrame(client.goods_tick_chart(EX_MARKET.US_STOCK, 'TSLA', date(2026, 3, 3))))
        print(pd.DataFrame(client.goods_chart_sampling(EX_MARKET.US_STOCK, 'TSLA')))
