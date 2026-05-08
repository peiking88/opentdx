# CLAUDE.md — opentdx 项目规范

## Git 认证

- 使用环境变量 `GIT_USERNAME` + `GIT_PASSWORD` 进行认证
- 设置远程仓库地址为 `https://github.com/用户名/项目名.git`
- 推送时拼接认证：`https://${GIT_USERNAME}:${GIT_PASSWORD}@{host}/{repo}.git`
- 推送完成后恢复无 token 的地址，避免泄露
- 将所有对 `https://bgithub.xyz` 的访问替换为 `https://github.com`
- `user.name` 设置为 `peiking88`，`user.email` 设置为 `peiking88@users.noreply.github.com`
- 不许用 `http.sslVerify=false`

## Git 访问

依次尝试以下地址，直到成功：

1. `https://github.com`（双向，优先）
2. `https://kkgithub.com`（双向）
3. `https://ghfast.top/https://github.com`（仅拉取）

提交前检查：确保 commit 中不包含 token、密码等敏感信息。

## Git 提交规范

- 每次提交前总结当前工作生成 `summary.md`
- 每次提交前自动更新 `README.md`
- commit message 和所有文档统一使用中文

## 编译

- ninja 或 make 使用 `-j$(nproc)` 参数并行编译

## 禁止事项

- 不修改 `external/` 下的源文件
- 不提交 `external/` 目录
- 不许用 `http.sslVerify=false`

## 测试

- 覆盖率 > 80%
- 同时支持真实与 mock 测试，真实测试优先级高于 mock
- 第三方组件不计入覆盖率，不做单元测试
- 用例不简化，不绕过问题
- 过程控制：建立 todo-list、跟踪进度

## 验收标准

- 阶段完成：所有单元测试通过才能进入下一阶段
- 全部完成：所有单元测试 + 集成测试通过
- 偏好：从国内镜像下载软件、依赖包、模型、数据

## 目录结构

项目标准目录：`docs`、`cfg`、`src`、`scripts`、`tests`、`output`

## 精度

数值输出格式规范：

- 价位、金额类：`%.2f`（保留两位小数）
- 数量类：`%d`（整数）
- 百分比：`%d%%`，如 `10%`，不用小数

## 语言

所有工作过程、生成文档、提交变更、README 统一使用中文。

## 初始化

项目初始化完成后检查环境完整性并报告。
