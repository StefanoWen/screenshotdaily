# 🤖 Copilot Instructions for screenshotdaily

## 项目架构与核心流程
- 本项目为自动化网页截图、推送 GitHub、并通过企业微信 webhook 发送图片的工具。
- 主脚本为 `screenshot_and_send.py`，CI 配置在 `.github/workflows/screenshot_and_send.yml`。
- 截图文件统一保存在 `screenshots/` 目录，CI 模式下自动清理，本地调试模式下自动 git add/commit/push。
- 企业微信消息始终发送 GitHub raw 图片链接，确保图片可访问。

## 主要开发/调试流程
- **本地调试**：
  1. 设置环境变量 `DEBUG_LOCAL=1`，`WECHAT_WEBHOOK_URL`。
  2. 运行 `python screenshot_and_send.py`，脚本会自动清空截图目录、截图、推送图片到 GitHub、发送企业微信消息。
  3. 本地调试时自动执行 git add/commit/push，确保图片上传后再发送消息。
- **CI 自动化**：
  - 通过 GitHub Actions 定时或手动触发，自动截图、推送、发送消息、清理截图。

## 关键约定与模式
- **URL 连通性检查**：截图前用 requests 检查 URL 可访问性，失败则跳过。
- **图片命名**：URL 转为文件名时用下划线替换斜杠，防止路径冲突。
- **环境变量**：
  - `WECHAT_WEBHOOK_URL`：企业微信机器人 webhook 地址（必填）
  - `DEBUG_LOCAL`：本地调试模式（1/0）
  - `GITHUB_REPOSITORY`、`GITHUB_REF_NAME`：自动推断，CI 环境自动注入
- **消息格式**：企业微信消息为 markdown_v2，图片用 `![](url)` 插入。
- **目录结构**：
  - `screenshot_and_send.py`：主逻辑脚本
  - `.github/workflows/screenshot_and_send.yml`：CI 配置
  - `screenshots/`：截图目录

## 常见问题与调试
- Playwright 超时：多为目标站点网络问题，脚本已内置 URL 检查。
- 图片链接 404：本地调试时需确保 git push 后再发送消息。
- CI 环境变量缺失：需在 GitHub Secrets 配置 `WECHAT_WEBHOOK_URL`。

## 典型用法示例
```bash
# 本地调试
export WECHAT_WEBHOOK_URL="..."
export DEBUG_LOCAL=1
python screenshot_and_send.py

# CI 自动化（无需手动操作）
# 见 .github/workflows/screenshot_and_send.yml
```

---
如需扩展功能（如自定义消息模板、支持更多平台），请参考主脚本注释和 README。
