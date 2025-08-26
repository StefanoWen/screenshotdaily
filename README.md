# 📸 Screenshot Daily - 自动截图工具

一个自动访问指定网址截图、推送到GitHub并发送到企业微信的自动化工具，支持CI环境自动调用和本地调试。

## ✨ 功能特性

- 🎯 **智能截图**: 支持多个URL自动截图，带有重试机制
- 🚀 **CI友好**: 完美适配GitHub Actions，支持自动触发
- 📱 **企业微信集成**: 自动发送截图到企业微信群
- 🔄 **自动清理**: CI模式下自动清理截图文件
- 🛠️ **灵活配置**: 支持命令行参数和环境变量配置
- 📊 **详细日志**: 完整的执行日志和错误处理

## 🚀 快速开始

### 本地运行

1. **安装依赖**
```bash
pip install playwright requests
playwright install chromium
```

2. **配置环境变量**
```bash
export WEBHOOK_KEY="你的企业微信webhook密钥"
export DEBUG_LOCAL="true"
```

3. **运行脚本**
```bash
# 使用默认配置
python screenshot_and_send.py

# 自定义URL
python screenshot_and_send.py --urls https://example.com https://google.com

# 启用详细日志
python screenshot_and_send.py --verbose

# 不发送webhook消息
python screenshot_and_send.py --no-webhook

# 不清理截图目录
python screenshot_and_send.py --no-cleanup
```

### CI环境运行

项目已配置GitHub Actions，支持以下触发方式：

#### 1. 定时任务
每天北京时间10:00自动执行

#### 2. 手动触发
在GitHub Actions页面手动运行，可自定义参数：
- **URLs**: 要截图的URL列表（空格分隔）
- **Verbose**: 启用详细日志输出

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `WEBHOOK_KEY` | 企业微信机器人webhook密钥 | 无 |
| `GITHUB_REPOSITORY` | GitHub仓库名 | 自动获取 |
| `GITHUB_REF_NAME` | GitHub分支名 | `main` |
| `DEBUG_LOCAL` | 本地调试模式 | `false` |
| `CI` | CI环境标志 | `false` |

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--urls` | 要截图的URL列表 | `--urls https://a.com https://b.com` |
| `--img-dir` | 截图保存目录 | `--img-dir custom_screenshots` |
| `--no-webhook` | 不发送webhook消息 | `--no-webhook` |
| `--no-cleanup` | 不清空截图目录 | `--no-cleanup` |
| `--verbose, -v` | 启用详细日志 | `--verbose` |

## 🏗️ 项目结构

```
.
├── screenshot_and_send.py      # 主脚本
├── .github/workflows/
│   └── screenshot_and_send.yml # GitHub Actions配置
├── screenshots/               # 截图保存目录（自动创建）
└── README.md                  # 说明文档
```

## 🔧 故障排除

### 常见问题

#### 1. Playwright超时错误
**问题**: `Page.goto: Timeout 30000ms exceeded`

**解决方案**:
- 检查网络连接
- 确认目标网站可访问
- 脚本已内置重试机制，会自动尝试更宽松的加载策略

#### 2. 企业微信webhook发送失败
**问题**: Webhook消息发送失败

**解决方案**:
- 检查`WEBHOOK_KEY`配置是否正确
- 确认企业微信机器人webhook密钥有效
- 查看详细日志了解具体错误

#### 3. CI环境截图失败
**问题**: GitHub Actions中截图失败

**解决方案**:
- 脚本已优化CI环境的浏览器启动参数
- 检查GitHub Secrets中的`WEBHOOK_KEY`配置
- 查看Actions日志了解详细错误信息

### 调试技巧

1. **启用详细日志**
```bash
python screenshot_and_send.py --verbose
```

2. **仅截图不发送消息**
```bash
python screenshot_and_send.py --no-webhook
```

3. **保留截图文件**
```bash
python screenshot_and_send.py --no-cleanup
```

## 📋 执行流程

1. **初始化**: 加载配置，创建截图目录
2. **清理**: 清空现有截图文件（可选）
3. **检查**: 验证URL可访问性
4. **截图**: 对每个URL执行截图任务
5. **推送**: 本地调试模式下推送到GitHub
6. **通知**: 发送企业微信webhook消息
7. **清理**: CI模式下清理截图文件

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

---

**提示**: 首次运行前请确保正确配置企业微信webhook地址和GitHub相关配置。
