# 工作摘要

**时间:** 2026-05-20 12:40:00

## 变更概要
- 修复分钟线 K 线解析器（K_Line）：upCount/downCount 检测对分钟线使用 to_datetime 验证替代 YYYYMMDD 启发式判断
- 增加 OHLC 逐字段边界检查，防止数据截断时 struct.unpack 越界
- get_price() 增加数据长度边界检查，防止 pos 超出 data 范围时崩溃
