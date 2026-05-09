# OpenTDX API 参考文档

> 版本 0.3.0 | 285 测试 | 90% 覆盖率

## 目录

- [快速开始](#快速开始)
- [TdxClient 统一入口](#tdxclient-统一入口)
- [QuotationClient A股行情](#quotationclient-a股行情)
- [exQuotationClient 扩展行情](#exquotationclient-扩展行情)
- [SP 协议板块接口](#sp-协议板块接口)
- [枚举类型](#枚举类型)
- [工具函数](#工具函数)

---

## 快速开始

```python
from opentdx import TdxClient
from opentdx.const import MARKET, PERIOD, ADJUST, CATEGORY, EX_MARKET

with TdxClient() as client:
    # A股
    client.stock_quotes(MARKET.SZ, '000001')
    client.stock_kline(MARKET.SH, '999999', PERIOD.DAILY)

    # 扩展市场
    client.goods_quotes(EX_MARKET.US_STOCK, 'TSLA')

    # SP协议板块
    qc = QuotationClient()
    qc.sp().get_board_members_quotes('880761', count=10)
```

---

## TdxClient 统一入口

门面类，聚合 QuotationClient 和 exQuotationClient，提供 `stock_*` 和 `goods_*` 系列方法。

### 连接管理

| 方法 | 签名 | 说明 |
|------|------|------|
| `__enter__` | `() -> TdxClient` | 上下文管理器，自动连接+登录 |
| `__exit__` | `(exc_type, exc_val, exc_tb)` | 退出时断开两个客户端 |
| `q_client` | `() -> QuotationClient` | 获取A股客户端（自动重连） |
| `eq_client` | `() -> exQuotationClient` | 获取扩展市场客户端（自动重连） |

### A股接口 (stock_* 系列)

所有方法转发到 `q_client()`，参数与返回值与 QuotationClient 对应方法一致。

| TdxClient 方法 | 等价于 | 说明 |
|---------------|--------|------|
| `stock_count(market)` | `q_client().get_count(market)` | 股票数量 |
| `stock_list(market, start, count)` | `q_client().get_list(...)` | 股票列表 |
| `stock_kline(market, code, period, start, count, times, adjust)` | `q_client().get_kline(...)` | K线数据 |
| `stock_quotes(code_list, code)` | `q_client().get_quotes(...)` | 简略报价 |
| `stock_quotes_detail(code_list, code)` | `q_client().get_stock_quotes_details(...)` | 5档详细报价 |
| `stock_quotes_list(category, start, count, sort_type, reverse, filter)` | `q_client().get_stock_quotes_list(...)` | 分类行情列表 |
| `stock_top_board(category)` | `q_client().get_stock_top_board(...)` | 排行榜 |
| `stock_tick_chart(market, code, date, start, count)` | `q_client().get_tick_chart(...)` | 分时图 |
| `stock_transaction(market, code, date)` | `q_client().get_transaction(...)` | 逐笔成交 |
| `stock_unusual(market, start, count)` | `q_client().get_unusual(...)` | 异动数据 |
| `stock_auction(market, code)` | `q_client().get_auction(...)` | 竞价数据 |
| `stock_history_orders(market, code, date)` | `q_client().get_history_orders(...)` | 历史委托 |
| `stock_chart_sampling(market, code)` | `q_client().get_chart_sampling(...)` | 分时缩略 |
| `stock_f10(market, code)` | `q_client().get_company_info(...)` | F10公司信息 |
| `stock_block(block_type)` | `q_client().get_block_file(...)` | 板块文件 |
| `stock_vol_profile(market, code)` | `q_client().get_vol_profile(...)` | 成交分布 |
| `index_momentum(market, code)` | `q_client().get_index_momentum(...)` | 指数动量 |
| `index_info(code_list, code)` | `q_client().get_index_info(...)` | 指数概况 |

### 扩展市场接口 (goods_* 系列)

| TdxClient 方法 | 等价于 | 说明 |
|---------------|--------|------|
| `goods_count()` | `eq_client().get_count()` | 商品数量 |
| `goods_category_list()` | `eq_client().get_category_list()` | 分类列表 |
| `goods_list(start, count)` | `eq_client().get_list(...)` | 商品列表 |
| `goods_quotes(code_list, code)` | `eq_client().get_quotes(...)` | 商品报价 |
| `goods_quotes_list(market, start, count, sortType, reverse)` | `eq_client().get_quotes_list(...)` | 行情列表 |
| `goods_kline(market, code, period, start, count, times)` | `eq_client().get_kline(...)` | K线 |
| `goods_tick_chart(market, code, date)` | `eq_client().get_tick_chart(...)` | 分时图 |
| `goods_history_transaction(market, code, date)` | `eq_client().get_history_transaction(...)` | 历史成交 |
| `goods_chart_sampling(market, code)` | `eq_client().get_chart_sampling(...)` | 分时缩略 |

### 兼容辅助方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `stock_xdxr` | `(market: MARKET, code: str) -> list[dict]` | 除息除权信息（tdxpy兼容） |
| `stock_finance` | `(market: MARKET, code: str) -> dict` | 财务信息（tdxpy兼容） |
| `stock_k_data` | `(code: str, start_date: str, end_date: str) -> DataFrame` | K线DataFrame（tdxpy兼容） |
| `get_traffic_stats` | `() -> dict` | 流量统计 |

---

## QuotationClient A股行情

### 连接

| 方法 | 签名 | 说明 |
|------|------|------|
| `connect` | `(ip=None, port=7709, time_out=5, bind_port=None, bind_ip='0.0.0.0')` | TCP连接（自动选最快IP） |
| `login` | `(show_info=False) -> bool` | 登录认证 |
| `disconnect` | `()` | 断开连接 |
| `doHeartBeat` | `()` | 发送心跳包 |

### 获取数据

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| `get_count` | `(market: MARKET) -> int` | 股票数量 | 深圳/上海/北交所 |
| `get_list` | `(market: MARKET, start=0, count=0) -> list[dict]` | `[{code, name, vol, pre_close, ...}]` | 股票列表（count=0取全部） |
| `get_kline` | `(market, code, period: PERIOD, start=0, count=800, times=1, adjust=ADJUST.NONE) -> list[dict]` | `[{datetime, open, high, low, close, vol, amount, turnover}]` | K线，支持复权 |
| `get_quotes` | `(all_stock, code=None) -> list[dict]` | `[{market, code, close, open, ...}]` | 简略报价（1档盘口） |
| `get_stock_quotes_details` | `(code_list, code=None) -> list[dict]` | `[{..., handicap: {bid, ask}}]` | 5档详细报价 |
| `get_stock_quotes_list` | `(category, start=0, count=80, sort_type, reverse, filter) -> list[dict]` | 分类行情列表 | 支持排序+过滤 |
| `get_stock_top_board` | `(category: CATEGORY) -> dict` | `{increase, decrease, amplitude, ...}` | 排行榜 |
| `get_tick_chart` | `(market, code, date=None, start=0, count=47616) -> list[dict]` | `[{price, avg, vol}]` | 实时/历史分时图 |
| `get_transaction` | `(market, code, date=None) -> list[dict]` | `[{time, price, vol, num, action}]` | 逐笔成交 |
| `get_unusual` | `(market, start=0, count=0) -> list[dict]` | `[{index, market, code, time, desc, value}]` | 异动数据 |
| `get_auction` | `(market, code) -> list[dict]` | `[{time, price, matched, unmatched}]` | 竞价数据 |
| `get_history_orders` | `(market, code, date) -> list[dict]` | `[{price, vol}]` | 历史委托 |
| `get_chart_sampling` | `(market, code) -> list[float]` | 价格采样点 | 分时缩略图 |
| `get_company_info` | `(market, code) -> list[dict]` | `[{name, content}]` | F10+XDXR+财报 |
| `get_block_file` | `(block_file_type: BLOCK_FILE_TYPE)` | 板块文件 | 下载+解析 |
| `get_index_info` | `(all_stock, code=None) -> list[dict]` | `[{market, code, open, close, up_count, ...}]` | 指数概况 |
| `get_index_momentum` | `(market, code) -> list[int]` | 动量列表 | 指数动量 |
| `get_vol_profile` | `(market, code) -> list[dict]` | `[{price, vol, buy, sell}]` | 成交分布 |
| `download_file` | `(filename, filesize=0, report_hook=None) -> bytearray` | 文件内容 | 下载服务器文件 |
| `get_text_file` | `(filename, sep='\|') -> list[str]` | 文本行列表 | 下载+解析文本文件 |

### SP 模式

调用 `sp()` 后可用 SP 协议板块接口（见[SP 协议板块接口](#sp-协议板块接口)）。

```python
qc = QuotationClient(True, True)
qc.connect().login()
qc.sp()  # 切换到 SP 模式
qc.get_board_list(BOARD_TYPE.HY)
```

---

## exQuotationClient 扩展行情

连接方法同 QuotationClient，端口为 7727。

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_count` | `() -> int` | 商品数量 |
| `get_category_list` | `() -> list[dict]` | 市场分类列表 |
| `get_list` | `(start=0, count=2000) -> list[dict]` | 商品列表 |
| `get_quotes` | `(code_list, code=None) -> list[dict]` | 批量报价 |
| `get_quotes_single` | `(market, code) -> dict` | 单只报价 |
| `get_quotes_list` | `(market, start=0, count=100, sortType, reverse) -> list[dict]` | 分类行情列表 |
| `get_kline` | `(market, code, period, start=0, count=800, times=1) -> list[dict]` | K线 |
| `get_tick_chart` | `(market, code, date=None) -> list[dict]` | 分时图 |
| `get_history_transaction` | `(market, code, date) -> list[dict]` | 历史成交 |
| `get_chart_sampling` | `(market, code) -> list[float]` | 分时缩略 |
| `get_history_instrument_bars_range` | `(market, code, start_date, end_date) -> list[dict]` | 按日期范围取K线 |
| `get_instrument_info` | `(start=0, count=100) -> list[dict]` | 商品元信息 |
| `server_info` | `()` | 服务器信息 |
| `download_file` | `(filename, filesize=0, report_hook=None)` | 下载文件 |
| `get_table` | `()` | 表格数据 |

---

## SP 协议板块接口

通过 `CommonClientMixin` 混入，需先调用 `sp()`:

```python
client.sp().get_board_members_quotes('880761', count=10)
```

### 板块查询

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_board_count` | `(market: BOARD_TYPE \| EX_BOARD_TYPE)` | 板块数量 |
| `get_board_list` | `(market, count=10000) -> list` | 板块列表（行业/地区/概念/港股/美股） |
| `get_board_members` | `(board_symbol, count=100000, sort_type, sort_order) -> list` | 板块成分股 |
| `get_board_members_quotes` | `(board_symbol, count=100000, sort_type, sort_order, fields) -> list` | 板块成分股实时行情 |
| `top_board_members` | `(board_symbol, count=20) -> list` | 板块活跃成分股排行榜 |
| `count_board_members` | `(board_symbol, count=1, ...)` | 板块成分数量 |

### 个股查询

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_symbol_bars` | `(market, code, period, times=1, start=0, count=800, fq=ADJUST.NONE) -> list` | 统一K线（A股/港股/美股/期货） |
| `get_symbol_quotes` | `(code_list, fields=None) -> dict` | 多股票批量行情（自定义字段） |
| `get_symbol_tick_chart` | `(market, code, query_date=None) -> dict` | 分时图（支持历史日期） |
| `get_symbol_transactions` | `(market, code, count=100000, start=0, query_date=None) -> list` | 逐笔成交 |
| `get_symbol_zjlx` | `(symbol, market: MARKET) -> DataFrame` | 资金流向 |
| `get_symbol_belong_board` | `(symbol, market) -> DataFrame` | 所属板块 |
| `get_market_monitor` | `(market: MARKET, start=0, count=10) -> list[dict]` | 主力监控（无需登录） |

### 自定义字段

使用 `FieldBit` / `PresetField` / `FieldSelection` 精确控制返回字段：

```python
from opentdx.utils.bitmap import FieldBit, PresetField

# 预设字段集
fields = PresetField.BASIC       # 基础OHLCV
fields = PresetField.QUOTE       # 盘口
fields = PresetField.FUNDAMENTAL # 基本面

# 组合字段
fields = PresetField.BASIC + FieldBit.AH_CODE + FieldBit.LOT_SIZE

mqc.get_board_members_quotes('880761', count=10, fields=fields)
```

---

## 枚举类型

### MARKET — A股市场

```python
MARKET.SZ = 0   # 深圳
MARKET.SH = 1   # 上海
MARKET.BJ = 2   # 北交所
```

### EX_MARKET — 扩展市场

```python
EX_MARKET.US_STOCK        # 美股
EX_MARKET.HK_MAIN_BOARD   # 港股主板
EX_MARKET.HK_GEM_BOARD    # 港股创业板
EX_MARKET.SH_FUTURES      # 上海期货
EX_MARKET.CFFEX_FUTURES   # 中金所期货
EX_MARKET.DCE_FUTURES     # 大商所期货
EX_MARKET.CZCE_FUTURES    # 郑商所期货
EX_MARKET.INE_FUTURES     # 上海能源期货
EX_MARKET.SH_OPTION       # 上海期权
EX_MARKET.SZ_OPTION       # 深圳期权
```

### PERIOD — K线周期

```python
PERIOD.MIN_1    # 1分钟
PERIOD.MIN_5    # 5分钟
PERIOD.MIN_15   # 15分钟
PERIOD.MIN_30   # 30分钟
PERIOD.MIN_60   # 60分钟
PERIOD.DAILY    # 日线
PERIOD.WEEKLY   # 周线
PERIOD.MONTHLY  # 月线
PERIOD.QUARTERLY# 季线
PERIOD.YEARLY   # 年线
```

### ADJUST — 复权类型

```python
ADJUST.NONE     = 0  # 不复权
ADJUST.QFQ      = 1  # 前复权
ADJUST.HFQ      = 2  # 后复权
```

### CATEGORY — 市场分类

```python
CATEGORY.A      # A股
CATEGORY.SH     # 上证A
CATEGORY.SZ     # 深证A
CATEGORY.KCB    # 科创板
CATEGORY.BJ     # 北证A
CATEGORY.CYB    # 创业板
CATEGORY.B      # B股
```

### SORT_TYPE — 排序类型

```python
SORT_TYPE.CODE          # 代码
SORT_TYPE.CHANGE_PCT    # 涨跌幅
SORT_TYPE.VOLUME        # 成交量
SORT_TYPE.AMOUNT        # 成交额
SORT_TYPE.PRICE         # 价格
SORT_TYPE.TOTAL_AMOUNT  # 总金额
SORT_TYPE.ACTIVITY      # 活跃度
```

### BOARD_TYPE — 板块类型

```python
BOARD_TYPE.HY       # 通达信普通行业一级分类 (127)
BOARD_TYPE.HY2      # 通达信普通行业二级分类 (344)
BOARD_TYPE.GN       # 概念板块 (269)
BOARD_TYPE.FG       # 风格板块 (158)
BOARD_TYPE.DQ       # 地区板块 (32)
BOARD_TYPE.ALL      # 全部板块 (559)
```

### BLOCK_FILE_TYPE — 板块文件

```python
BLOCK_FILE_TYPE.DEFAULT  # 一般板块 block.dat
BLOCK_FILE_TYPE.ZS       # 指数板块 block_zs.dat
BLOCK_FILE_TYPE.FG       # 风格板块 block_fg.dat
BLOCK_FILE_TYPE.GN       # 概念板块 block_gn.dat
```

---

## 工具函数

### to_df — 数据转DataFrame

```python
from opentdx import to_df

to_df([{"a": 1}, {"a": 2}])  # → DataFrame
to_df({"a": 1})               # → 单行DataFrame
to_df(None)                   # → 空DataFrame
```

### 异常类

```python
from opentdx.exceptions import (
    TdxConnectionError,      # 连接失败
    TdxFunctionCallError,    # 函数调用失败
    ValidationException,     # 参数验证失败
)
```

### 位图工具

```python
from opentdx.utils.bitmap import FieldBit, PresetField, FieldSelection

# 单个字段
FieldBit.PRE_CLOSE, FieldBit.OPEN, FieldBit.CLOSE, FieldBit.VOL

# 预设组合
PresetField.BASIC       # 基础OHLCV (6字段)
PresetField.ENHANCED    # 增强
PresetField.COMMON      # 通用
PresetField.QUOTE       # 盘口
PresetField.VOLUME      # 量能
PresetField.FUNDAMENTAL # 基本面

# 组合
sel = PresetField.BASIC + FieldBit.AH_CODE
sel = PresetField.BASIC | PresetField.QUOTE
```
