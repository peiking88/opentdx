# 工作摘要

**时间:** 2026-05-09

## 变更概要

新增三个通达信本地数据交互接口，支持通信配置自动检测、本地数据校验、复权因子下载。

### 新增文件

| 文件 | 说明 |
|------|------|
| `opentdx/reader/connect_cfg_reader.py` | TdxConnectCfgReader — 解析 connect.cfg (GBK INI)，获取行情主站等服务器配置 |
| `opentdx/utils/vipdoc_validator.py` | VipdocValidator — 扫描 vipdoc 各市场/周期数据文件，校验最新日期和完整性 |
| `opentdx/crawler/adjustment_factor_crawler.py` | AdjustmentFactorCrawler — 通过 XDXR 协议下载除权除息数据，支持 QFQ/HFQ 因子计算 |
| `tests/test_connect_cfg_reader.py` | 9 个测试用例 |
| `tests/test_vipdoc_validator.py` | 15 个测试用例 |
| `tests/test_adjustment_factor_crawler.py` | 20 个测试用例 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `opentdx/__init__.py` | 导出三个新类 |
| `opentdx/reader/__init__.py` | 导出 TdxConnectCfgReader |
| `opentdx/crawler/__init__.py` | 导出 AdjustmentFactorCrawler |

### 配置改进

- 路径类参数支持通过环境变量 `TDX_HOME` 配置
- 构造函数均接受自定义路径参数

## 测试结果

332 个测试用例全部通过（47 个新增）。
