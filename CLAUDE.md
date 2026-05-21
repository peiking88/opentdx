# CLAUDE.md — opentdx 项目规范

> 通用编码准则（先思考再编码、简单优先、精准修改、目标驱动执行）见全局 `~/.claude/CLAUDE.md`。
> 本文件仅包含 opentdx 项目特定规则和覆盖项。

## 项目信息

- 仓库：`github.com/peiking88/opentdx`
- 版本管理：源码 `__version__`，格式 `x.y.z`（无 `v` 前缀）
- Python 项目，使用虚拟环境

## Git 远程访问

依次尝试以下镜像，直到成功：

1. `https://ghfast.top/https://github.com`
2. `https://kkgithub.com`
3. `https://github.com`

认证：环境变量 `GIT_USERNAME` + `GIT_PASSWORD`，推送完成后恢复无 token 地址。
禁止 `http.sslVerify=false`。

## Git 提交规范

每次提交前自动执行：

1. 生成 `summary.md` 总结当前工作（已在 `.gitignore`，不提交）
2. 更新 `README.md`
3. 按规则升版本号并打 tag：
   - 增加功能 → 升次版本号（minor）
   - 修改缺陷 → 升三级版本号（patch）
   - 升主版本号（major）→ 征求用户意见
4. 同步更新源码 `__version__`
5. 检查敏感信息：commit 不含 token、密码

commit message 使用中文。

## 测试

- 覆盖率 > 80%
- 真实测试优先于 mock，非必要不 mock
- 真实测试返回数量 > 50 时，改为验证样本或验证总数
- 第三方组件不计入覆盖率，不做单元测试
- 用例不简化、不跳过
- 先激活虚拟环境再运行测试

## 需求规范

- 批处理长任务支持 `-n` 参数控制并发数
- 批处理长任务支持中断重试和续跑（断点续传）
- 路径类参数可配置（环境变量或配置文件）

## 编译

ninja / make 使用 `-j$(nproc)` 并行编译。

## 精度（金融数据）

- 价位、金额：`%.2f`（保留两位小数）
- 数量：`%d`（整数）
- 百分比：`%d%%`（如 `10%`，不用小数）

## 目录结构

标准目录：`docs`、`cfg`、`src`、`scripts`、`tests`、`output`
chromium snap：`~/snap/bin/chromium`

## 禁止事项

- 不修改、不提交 `external/` 目录
- 适配依赖库新版本前先阅读其 API 文档

## 代码审计

排查 exception 使用：该用未用、不该用却用、异常类使用不当。
