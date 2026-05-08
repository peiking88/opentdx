# 工作摘要

**时间:** 2026-05-09

## 版本 0.3.0 变更概要

### 架构优化
- 修复 BaseParser.head 线程安全问题（serialize 中类属性变异）
- 修复 macQuotationClient/macExQuotationClient 钻石继承
- TdxClient 从 759 行精简到 170 行（__getattr__ + 分发表）
- commonClientMixin 5 处手写分页统一为 _paginate（-80 行）

### tdxpy 兼容层合并
- 删除 compat/ 目录，功能合并到原生层
- get_history_instrument_bars_range / get_instrument_info 加入 exQuotationClient
- get_traffic_stats 加入 BaseStockClient
- to_df 提取为独立工具函数
- 异常类移至 opentdx/exceptions.py

### Bug 修复
- get_symbol_bars 返回空列表（result.get('bars') → 'charts'）
- get_symbol_tick_chart 缺少 chart_data 字段
- 测试中 MARKET.XX.value 枚举比较错误

### 测试增强
- 测试数：195 → 285（+90）
- 覆盖率：71% → 90%（+19pp）
- 新增 test_mock_client.py（33 个 mock 客户端测试）
- 新增 TestTdxClientXDXR（7 个 XDXR 深度验证测试）
- 补强 20+ 个测试的值断言（价格/代码/日期验证）
- 真实测试 144 > Mock 测试 141
