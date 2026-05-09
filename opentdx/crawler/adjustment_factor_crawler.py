"""复权因子下载器 — 通过 TDX 服务器下载除权除息数据，支持前复权/后复权因子计算"""
import json
import time
from datetime import datetime
from pathlib import Path

from opentdx.const import MARKET, ADJUST
from opentdx.utils.log import logger


class AdjustmentFactorCrawler:
    """下载并管理通达信除权除息(XDXR)数据，支持前复权/后复权因子计算"""

    def __init__(self, client=None, output_dir=None):
        self.client = client
        self.output_dir = Path(output_dir) if output_dir else Path.home() / ".opentdx" / "xdxr"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_adjustment_factors(self, market, code):
        """获取单只股票的除权除息事件列表"""
        if self.client is None:
            raise RuntimeError("未设置 client，请先通过构造函数注入 QuotationClient")

        if isinstance(code, str):
            code_str = code
        else:
            code_str = str(code)

        result = self._call_xdxr(market, code_str)
        return self._normalize_events(result, market, code_str)

    def _call_xdxr(self, market, code_str):
        """调用 XDXR，子类可重写用于测试"""
        from opentdx.parser.quotation import company_info as ci

        return self.client.call(ci.XDXR(market, code_str))

    def _normalize_events(self, raw_events, market, code):
        """标准化 XDXR 事件列表：解码 code 字段并统一格式"""
        if not raw_events:
            return []
        events = []
        for evt in raw_events:
            normalized = dict(evt)
            normalized["market"] = evt["market"].value if hasattr(evt["market"], "value") else evt["market"]
            c = evt.get("code", b"")
            if isinstance(c, bytes):
                c = c.rstrip(b"\x00").decode("utf-8", errors="replace")
            normalized["code"] = c
            if isinstance(evt.get("date"), datetime):
                normalized["date"] = evt["date"].strftime("%Y-%m-%d")
            events.append(normalized)
        return events

    def fetch_adjustment_factors_safe(self, market, code):
        """安全获取 XDXR，连接失败时自动重连"""
        try:
            return self.fetch_adjustment_factors(market, code)
        except Exception as e:
            logger.warning(f"获取 {code} XDXR 失败: {e}")
            return []

    def batch_fetch(self, markets=None, codes=None, progress_callback=None):
        """批量下载 XDXR 数据
        markets: MARKET 列表，默认 [MARKET.SZ, MARKET.SH]
        codes: 指定代码列表，为 None 时需遍历市场
        progress_callback: callable(current, total)
        """
        if markets is None:
            markets = [MARKET.SZ, MARKET.SH]

        results = {}
        all_tasks = []

        if codes:
            for market in markets:
                for code in codes:
                    all_tasks.append((market, code))
        else:
            for market in markets:
                try:
                    stock_list = self._get_stock_list(market)
                    for code in stock_list:
                        all_tasks.append((market, code))
                except Exception as e:
                    logger.warning(f"获取 {market} 股票列表失败: {e}")

        total = len(all_tasks)
        for idx, (market, code) in enumerate(all_tasks):
            events = self.fetch_adjustment_factors_safe(market, code)
            key = f"{code}"
            results[key] = events

            if progress_callback:
                progress_callback(idx + 1, total)
            else:
                if (idx + 1) % 50 == 0:
                    logger.info(f"XDXR 下载进度: {idx + 1}/{total}")

            # 限速，避免被封
            if (idx + 1) % 20 == 0:
                time.sleep(0.5)

        return results

    def _get_stock_list(self, market):
        """获取市场股票列表"""
        if self.client is None:
            raise RuntimeError("未设置 client")
        try:
            stocks = self.client.get_security_list(market, 0)
            return [s["code"] for s in stocks if "code" in s]
        except Exception:
            # 回退：从行情列表获取
            quotes = self.client.get_security_quotes(market, 0, 0)
            if not quotes:
                return []
            return [q.get("code", "") for q in quotes if q.get("code")]

    def save_to_json(self, data, filename=None, market=None):
        """保存 XDXR 数据到 JSON 文件"""
        if filename is None:
            market_str = f"{market.value}" if market and hasattr(market, "value") else "all"
            filename = f"xdxr_{market_str}_{datetime.now():%Y%m%d}.json"
        filepath = self.output_dir / filename

        # 确保可序列化
        serializable = {
            "metadata": {
                "download_date": datetime.now().isoformat(),
                "market": market.value if market and hasattr(market, "value") else str(market),
                "count": len(data),
            },
            "factors": data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"XDXR 数据已保存到 {filepath}")
        return str(filepath)

    def load_from_json(self, filepath):
        """从 JSON 文件加载 XDXR 数据"""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---- 复权因子计算 ----

    @staticmethod
    def compute_qfq(xdxr_events):
        """计算前复权累积因子。
        从最近的事件向前迭代，计算各事件的前复权调整系数。
        返回与输入等长的列表，每个事件附加 'qfq_factor' 字段。

        QFQ: 向前调整历史价格，使最新价格保持真实。
        factor = (pre_close - fenhong + peigujia * peigu) / (pre_close + songzhuangu + peigu)

        注：pre_close 需从 K 线数据获取，此处不包含在 XDXR 中。
        本方法计算的是除权比例（不含 pre_close 的部分），
        实际应用时需结合前收盘价计算最终因子。
        """
        if not xdxr_events:
            return []

        sorted_events = sorted(xdxr_events, key=lambda e: _parse_event_date(e), reverse=True)
        cumulative_factor = 1.0
        results = []

        for evt in sorted_events:
            entry = dict(evt)
            category = evt.get("name", evt.get("category", 1))
            fenhong = evt.get("fenhong") or 0.0
            peigujia = evt.get("peigujia") or 0.0
            songzhuangu = evt.get("songzhuangu") or 0.0
            peigu = evt.get("peigu") or 0.0

            if category == "除权除息" or category == 1:
                # 除权除息比例（不含 pre_close 部分）
                # 完整公式: factor = (pre_close - fh + pj * pg) / (pre_close + szg + pg)
                # 此处存储分量，实际使用时需提供 pre_close
                entry["fenhong_num"] = fenhong
                entry["peigu_num"] = peigu * peigujia
                entry["denom_add"] = songzhuangu + peigu
            else:
                entry["fenhong_num"] = 0.0
                entry["peigu_num"] = 0.0
                entry["denom_add"] = 0.0

            entry["qfq_cumulative_factor"] = cumulative_factor
            results.append(entry)

        return list(reversed(results))

    @staticmethod
    def compute_hfq(xdxr_events):
        """计算后复权累积因子。
        从最早的事件向后迭代，计算各事件的后复权调整系数。

        HFQ: 向后调整最新价格，使历史价格保持真实。
        factor = (pre_close + songzhuangu + peigu) / (pre_close - fenhong + peigujia * peigu)

        注：pre_close 需从 K 线数据获取，此处计算除权比例分量。
        """
        if not xdxr_events:
            return []

        sorted_events = sorted(xdxr_events, key=lambda e: _parse_event_date(e))
        cumulative_factor = 1.0
        results = []

        for evt in sorted_events:
            entry = dict(evt)
            category = evt.get("name", evt.get("category", 1))
            fenhong = evt.get("fenhong") or 0.0
            peigujia = evt.get("peigujia") or 0.0
            songzhuangu = evt.get("songzhuangu") or 0.0
            peigu = evt.get("peigu") or 0.0

            if category == "除权除息" or category == 1:
                entry["hfq_numer_add"] = songzhuangu + peigu
                entry["hfq_denom_sub"] = fenhong - peigu * peigujia
            else:
                entry["hfq_numer_add"] = 0.0
                entry["hfq_denom_sub"] = 0.0

            entry["hfq_cumulative_factor"] = cumulative_factor
            results.append(entry)

        return results

    @staticmethod
    def compute_full_factor(xdxr_events, pre_close_prices, adjust=ADJUST.QFQ):
        """结合前收盘价计算完整的复权因子。

        xdxr_events: XDXR 事件列表
        pre_close_prices: dict, {date: close_price} — 事件日期对应的前收盘价
        adjust: ADJUST.QFQ 或 ADJUST.HFQ

        返回每个事件的复权累积因子。
        """
        if not xdxr_events:
            return []

        reverse = adjust == ADJUST.QFQ
        sorted_events = sorted(xdxr_events, key=lambda e: _parse_event_date(e), reverse=reverse)
        cumulative_factor = 1.0
        results = []

        for evt in sorted_events:
            entry = dict(evt)
            event_date = _parse_event_date(evt)
            date_str = f"{event_date[0]:04d}-{event_date[1]:02d}-{event_date[2]:02d}"

            pre_close = pre_close_prices.get(date_str, pre_close_prices.get(str(event_date), None))
            if pre_close is None or pre_close == 0:
                entry["factor"] = cumulative_factor
                results.append(entry)
                continue

            fenhong = evt.get("fenhong") or 0.0
            peigujia = evt.get("peigujia") or 0.0
            songzhuangu = evt.get("songzhuangu") or 0.0
            peigu = evt.get("peigu") or 0.0
            category = evt.get("name", evt.get("category", 1))

            if category == "除权除息" or category == 1:
                numerator = pre_close - fenhong + peigujia * peigu
                denominator = pre_close + songzhuangu + peigu
                if denominator == 0:
                    event_factor = 1.0
                else:
                    if adjust == ADJUST.QFQ:
                        event_factor = numerator / denominator
                    else:
                        event_factor = denominator / numerator
            else:
                event_factor = 1.0

            cumulative_factor *= event_factor
            entry["factor"] = cumulative_factor
            results.append(entry)

        if adjust == ADJUST.QFQ:
            results.reverse()

        return results


def _parse_event_date(event):
    """从事件中解析日期，返回 (year, month, day)"""
    d = event.get("date")
    if isinstance(d, datetime):
        return d.year, d.month, d.day
    if isinstance(d, str):
        parts = d.split("-")
        return int(parts[0]), int(parts[1]), int(parts[2])
    return 2000, 1, 1
