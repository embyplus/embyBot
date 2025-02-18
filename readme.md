## Emby Bot 项目

本项目是一个基于 Telethon 的 Telegram Bot，用于管理 Emby 用户、发送邀请码、查询 Emby 资源等操作。同时集成了针对 Emby
路由服务的切换功能。项目主要通过 Python + SQLAlchemy + Telethon 实现。

### 功能概述
#### 用户管理：
- 根据邀请码创建 Emby 用户，并分配默认密码、默认策略等。
- 提供管理员命令禁用/解禁用户的 Emby 账号。
- 可查看用户当前信息（白名单、管理员身份、禁用状态等）。
#### 邀请码管理：
- 生成普通邀请码、白名单邀请码。
- 使用邀请码后自动更新数据库和相关标识。
#### 线路管理：
- 集成路由服务 API，允许用户在机器人对话中快速切换观影线路。
#### 其他辅助功能：
- 查看当前 Emby 影片数量。
- 限时或限量开放注册。

### 安装及运行
```bash
git clone https://github.com/embyplus/embyBot
cp .env.example .env
vim .env

python3 -m pip install -r requirements.txt
python3 app.py
```

### 配置环境变量

| 变量名	              | 说明	                                               | 示例值                        |
|-------------------|---------------------------------------------------|----------------------------|
| TIMEZONE          | 时区设置                                              | Asia/Shanghai              |
 | LOG_LEVEL         | 日志级别，可选 DEBUG / INFO / WARNING / ERROR / CRITICAL | INFO                       |
 | BOT_TOKEN         | 你的 Telegram Bot 令牌                                | 123456:ABC-DEF1234ghIkl... |
 | API_ID            | Telegram API ID（从 my.telegram.org 获取）             | 1234567                    |
 | API_HASH          | Telegram API Hash                                 | abcdef1234567890ghijklmn   |
 | TELEGRAM_GROUP_ID | Bot 要监听或管理的群组 ID，支持多群可用逗号分隔                       | -1001234567890             |
 | EMBY_URL          | Emby 服务器 URL                                      | https://your-emby-url      |
 | EMBY_API_KEY      | Emby 服务器 API Key                                  | embyapikey123              |
 | API_URL           | 路由服务 API 基础地址                                     | https://your-router-api    |
 | API_KEY           | 路由服务使用的鉴权 token，不需要则可留空                           | routerapikey123            |
 | DB_HOST           | 数据库主机名或 IP                                        | 127.0.0.1                  |
 | DB_PORT           | 数据库端口                                             | 3306                       |
 | DB_USER           | 数据库用户名                                            | root                       |
 | DB_PASS           | 数据库密码                                             | password                   |
 | DB_NAME           | 数据库名                                              | emby_bot_db                |
 | ADMIN_LIST        | Bot 管理员的 Telegram ID 列表（用逗号分隔）                    | 123456789,987654321        |

## 贡献指南
欢迎贡献代码！为了确保项目的高质量和一致性，请遵循以下贡献规程：
### 提交规范
- 提交信息必须符合 Angular 提交信息规范，格式如下：
  - `type(scope): description`
  - 例如：`feat(user): 添加用户注册功能`
### 与数据库、API 代码相关的更改
- 请确保所有更改都经过严格的测试，并且不会引入新的错误。
### 创建 Pull Request
- 请确保创建 Pull Request 前进行本地测试，确保通过所有 CI/CD 测试。
### 支持的 Type 列表

| Type     | 描述                                                         |
|----------|-------------------------------------------------------------|
| feat     | 添加新功能，比如新增用户注册、功能扩展等                    |
| fix      | 修复 bug 或错误，解决问题的修改                           |
| docs     | 文档相关修改，如更新说明文档、README、注释等                 |
| style    | 代码格式、标点、空格等修改，不影响代码逻辑运行                |
| refactor | 代码重构，调整代码结构而不改变功能                          |
| perf     | 性能优化修改，提升效率或降低资源消耗                        |
| test     | 添加或更新测试代码，保证项目稳定性                         |
| chore    | 杂项维护，如依赖更新、构建脚本修改，不涉及代码逻辑            |
| ci       | 持续集成相关修改，如 GitHub Actions 工作流程优化              |

---
感谢您的贡献！


### Thanks

- [Telethon](https://docs.telethon.dev/) - Telegram API for Python
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL Toolkit and Object-Relational Mapping
- [Emby服管理bot by小草](https://github.com/xiaocao666tzh/EmbyBot)