# 工作摘要

**时间:** 2026-05-09

## 变更概要

修复 `parse_tdx_date()` 返回类型：`int` → `datetime.date`。0.5.4 中错误地将返回类型改为 int，导致下游 mootdx 中 `_convert_transactions` 调用 `datetime.datetime.combine(d, t)` 失败。恢复为返回 `datetime.date` 并增强输入容错性。

## 最近提交
```
049ff5a 升级版本号至 0.5.4 — 修复运行时缺陷、清理死代码、合并重复代码
b9cae3e 升级版本号至 0.5.3 — 落地自定义异常类，替换裸 Exception/RuntimeError/ValueError 为 TdxConnectionError/TdxFunctionCallError/ValidationException
b732407 升级版本号至 0.5.2 — 技术债务清理：移除未使用 imports、合并重复异常类、简化表达式
f58949d 升级版本号至 0.5.1 — 修复 NameError 缺陷
ea17327 fix: 修复 count_board_members() 中 BoardMembers → BoardMembersQuotes NameError
```
