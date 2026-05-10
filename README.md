# opentdx — Python TDX 量化行情数据接口

项目创意来自 [pytdx](https://github.com/rainx/pytdx)，感谢 [@rainx](https://github.com/rainx)。

> **声明**：本项目为个人学习项目，仅用于学习交流。严禁用于任何商业用途，更严禁滥用接口。
> 接口仍在持续演进中，可能会有大幅改动。如需生产级数据，推荐[通达信官方量化平台](https://help.tdx.com.cn/quant/)。

---

## 主要功能

| 功能 | 说明 | 亮点 |
|------|------|------|
| A股行情 | 深市/沪市/创业板/科创板/北交所 | 支持AH股关联查询 |
| 扩展行情 | 期货/港股/美股/期权/债券/基金 | 支持全球主要市场 |
| K线数据 | 1分/5分/日/周/月/季/年 | 支持前复权/后复权/即时换手率 |
| 分时图 | 实时/历史分时数据 | 240根K线 |
| 逐笔成交 | 实时/历史成交明细 | 买卖方向标识 |
| 排行榜 | 涨跌幅/振幅/量比/换手率/委比 | 8种排名维度 |
| 板块数据 | 行业/地区/概念板块及成分股 | SP协议板块K线 |
| 资金流向 | 主力/散户资金流向 | 多周期统计 |
| 异动监控 | 主力监控精灵 | 无需登录 |
| 复权因子 | 自动检测并下载除权除息数据 | 前复权/后复权因子计算 |
| 本地数据 | 通信配置读取、vipdoc数据校验 | 支持环境变量 TDX_HOME 配置路径 |
| F10资料 | 公司信息/财报/除权分红 | 一站式聚合 |

## 安装

```bash
pip install opentdx
```

## 快速上手

```python
from datetime import date
import pandas as pd
from opentdx import TdxClient
from opentdx.const import MARKET, CATEGORY, EX_MARKET, PERIOD, SORT_TYPE, ADJUST

with TdxClient() as client:

    # ── A股行情 ──
    client.stock_count(MARKET.SZ)                             # 股票数量
    client.stock_list(MARKET.SZ, count=5)                     # 股票列表
    client.stock_quotes(MARKET.SH, '600000')                  # 实时报价
    client.stock_kline(MARKET.SZ, '000001', PERIOD.DAILY,     # K线（支持复权）
                       adjust=ADJUST.QFQ)
    client.stock_tick_chart(MARKET.SZ, '000001',              # 历史分时图
                            date(2026, 3, 16))
    client.stock_top_board(CATEGORY.A)                        # 排行榜
    client.stock_f10(MARKET.SZ, '000001')                     # F10资料
    client.stock_xdxr(MARKET.SZ, '000001')                    # 除权除息记录

    # ── 扩展行情 ──
    client.goods_quotes(EX_MARKET.US_STOCK, 'TSLA')           # 美股报价
    client.goods_kline(EX_MARKET.US_STOCK, 'TSLA',            # 美股K线
                       PERIOD.DAILY)
    client.goods_quotes(EX_MARKET.HK_MAIN_BOARD, '00700')     # 港股报价

# ── SP协议板块 ──
from opentdx.client.quotationClient import QuotationClient
from opentdx.utils.bitmap import PresetField

qc = QuotationClient(True, True)
qc.connect().login()
qc.sp()                                                       # 启用SP模式
qc.get_board_members_quotes('880761', count=10,              # 板块成分股行情
                            fields=PresetField.BASIC)
```

## 探索

```bash
opentdx doc    # 交互式API演示
```

## 项目亮点

- **自动选服** — 并发测速所有服务器，自动选择延迟最低的节点
- **SP协议** — 板块成分股行情、资金流向、自定义字段选择、复权K线
- **tdxpy兼容** — 完全覆盖 pytdx API，无缝迁移
- **高覆盖率** — 332 个测试用例，90% 代码覆盖率
- **交互式文档** — `opentdx doc` 实时演示每个接口
- **简洁架构** — TdxClient 门面 170 行，解析器注册模式清晰
- **本地工具** — 通信配置自动检测、vipdoc 数据校验、复权因子下载

## 服务端地址

| 类型 | 端口 | 用途 |
|------|------|------|
| 39个A股主站 | 7709 | 深市/沪市/北交所行情 |
| 16个扩展市场 | 7727 | 港股/美股/期货行情 |
| 3个SP主站 | 7709 | 板块数据/资金流向 |
| 2个SP扩展 | 7727 | 港股/美股板块 |
| 16个券商节点 | 7709/80 | 券商托管节点（备用） |

## 相关项目

- [tdx_mcp](https://github.com/LisonEvf/tdx_mcp) — MCP Server 版本
- [pytdx](https://github.com/rainx/pytdx) — 原始项目

## API 文档

完整接口参考见 [API_REFERENCE.md](API_REFERENCE.md)

---

#量化交易 #TDX接口 #Python金融

[![Star History Chart](https://api.star-history.com/svg?repos=LisonEvf/opentdx&type=Date)](https://star-history.com/#LisonEvf/opentdx&Date)

### 2026-05-09 10:37:35
```
 API_REFERENCE.md                             |  59 ++++-
 README.md                                    |   5 +-
 opentdx/__init__.py                          |   7 +-
 opentdx/crawler/__init__.py                  |   2 +
 opentdx/crawler/adjustment_factor_crawler.py | 298 +++++++++++++++++++++++++
 opentdx/reader/__init__.py                   |   2 +
 opentdx/reader/connect_cfg_reader.py         | 118 ++++++++++
 opentdx/utils/vipdoc_validator.py            | 253 ++++++++++++++++++++++
 pyproject.toml                               |   2 +-
 summary.md                                   |  36 +++-
 tests/test_adjustment_factor_crawler.py      | 312 +++++++++++++++++++++++++++
 tests/test_connect_cfg_reader.py             | 203 +++++++++++++++++
 tests/test_vipdoc_validator.py               | 245 +++++++++++++++++++++
 13 files changed, 1530 insertions(+), 12 deletions(-)
```

### 2026-05-09 16:30:00
```
 README.md                                    |   3 +-
 opentdx/client/baseStockClient.py            |  19 ++--
 opentdx/client/commonClientMixin.py          |   3 +-
 opentdx/crawler/adjustment_factor_crawler.py |   5 +-
 opentdx/parser/ex_quotation/quotes.py        |   3 +-
 opentdx/parser/ex_quotation/quotes2.py       |   3 +-
 opentdx/parser/mac_quotation/symbol_belong_board.py | 3 +-
 opentdx/parser/quotation/quotes.py           |   3 +-
 opentdx/parser/quotation/quotes_detail.py    |   3 +-
 opentdx/parser/quotation/quotes_encrypt.py   |   3 +-
 opentdx/utils/block_reader.py                |   7 +-
 opentdx/utils/help.py                        |   3 +-
 pyproject.toml                               |   2 +-
 summary.md                                   |   2 +-
 tests/test_adjustment_factor_crawler.py      |   3 +-
 tests/test_mock_client.py                    |   3 +-
 tests/test_parser_mock.py                    |   3 +-
 17 files changed, 42 insertions(+), 28 deletions(-)
```

### 2026-05-09 13:18:07
```
 .gitignore                                       | 5 +++--
 API_REFERENCE.md => docs/API_REFERENCE.md        | 0
 CHANGELOG.md => docs/CHANGELOG.md                | 0
 summary.md => docs/summary.md                    | 8 ++++----
 TDXMACDStrategy.py => scripts/TDXMACDStrategy.py | 0
 demo_diff.py => scripts/demo_diff.py             | 0
 demo_ext.py => scripts/demo_ext.py               | 0
 7 files changed, 7 insertions(+), 6 deletions(-)
```

### 2026-05-09 19:23:10
```
 opentdx/__init__.py                        |  2 +-
 opentdx/const.py                           |  2 +-
 opentdx/crawler/base_crawler.py            |  2 +-
 opentdx/doc.py                             | 13 --------
 opentdx/enums/__init__.py                  |  6 +---
 opentdx/parser/baseParser.py               |  4 +--
 opentdx/parser/quotation/__init__.py       |  3 +-
 opentdx/parser/quotation/get_block_info.py | 18 ----------
 opentdx/reader/connect_cfg_reader.py       |  8 +----
 opentdx/utils/cache.py                     |  3 --
 opentdx/utils/date_utils.py                | 17 ----------
 opentdx/utils/help.py                      | 53 ++++++++++++++++--------------
 opentdx/utils/vipdoc_validator.py          |  8 +----
 pyproject.toml                             |  2 +-
 summary.md                                 | 24 +++++++++++---
```

### 2026-05-10 00:19:11
```
 opentdx/client/baseStockClient.py             |  27 +-
 opentdx/exceptions.py                         |  13 +-
 opentdx/parser/mac_quotation/symbol_quotes.py |   8 +-
 opentdx/parser/quotation/company_info.py      |   6 +-
 opentdx/parser/quotation/kline.py             |  12 +-
 opentdx/reader/daily_bar_reader.py            |   2 +-
 opentdx/utils/help.py                         |   6 +-
 opentdx/utils/helper.py                       |  14 +-
 pyproject.toml                                |   2 +-
 summary.md                                    |  20 +-
 tests/test_error_paths.py                     |  71 +++++
 tests/test_ex_quotation_client.py             |  51 +++-
 tests/test_mac_quotation_client.py            |  99 +++++--
 tests/test_mock_client.py                     | 370 --------------------------
 tests/{test_parser_mock.py => test_parser.py} |   6 +-
```

### 2026-05-10 13:42:29
```
 pyproject.toml                     |  2 +-
 summary.md                         |  7 +++---
 tests/test_mac_quotation_client.py | 45 ++++++++++++++++++++++----------------
 3 files changed, 31 insertions(+), 23 deletions(-)
```
