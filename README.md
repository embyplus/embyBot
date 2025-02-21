
<p align="center">
    <img src="https://github.com/user-attachments/assets/7fcbb16b-577d-4de2-b1b0-23ec9b839f17" alt="embyBot logo" width=200 height=200 />
</p>
<h1 align="center">embyBot</h1>
<p align="center">
    <em>⚡ The next-generation emby management bot</em>
</p>

<p align="center">
<a href="https://opensource.org/licenses/Apache-2.0">
<img src="https://img.shields.io/github/license/embyplus/embyBot" alt="license">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=edb641" alt="python">
<a href="https://www.python.org/dev/peps/pep-0008/">
<img src="https://img.shields.io/badge/code%20style-PEP%208-000000.svg?logo=python&logoColor=blue" alt="PEP 8">
</a>
<br />
<a href="https://github.com/astral-sh/ruff">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="ruff">
</a>
<a href="https://github.com/astral-sh/uv">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</a>
<a href="https://results.pre-commit.ci/latest/github/embyplus/embyBot/main">
    <img src="https://results.pre-commit.ci/badge/github/embyplus/embyBot/main.svg" alt="pre-commit" />
</a>
<a href="https://codecov.io/gh/embyplus/embyBot">
<img src="https://codecov.io/gh/embyplus/embyBot/branch/master/graph/badge.svg" alt="codecov"/>
</a>
</p>

> [!IMPORTANT]
> ⭐️ Thanks **everyone** who has contributed to the project, it means a lot!

## 📣 Introduction

A Telegram bot for managing **Emby**, developed with **Pyrogram** and using **MySQL** as the database.

## ✨ Features

### User Management:

- Create Emby users with invitation codes and assign default passwords and policies.
- Provide admin commands to disable/enable Emby accounts.
- View current user information (whitelist status, admin privileges, ban status, etc.).

### Invitation Code Management:

- Generate standard and whitelist invitation codes.
- Automatically update the database and relevant status after using an invitation code.

### Route Management:

- Integrate the routing service API to allow users to quickly switch playback routes through the bot.

### Other Features:

- View the current number of Emby media items.
- Support limited-time or limited-quantity registration.

## 🔰 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/embyplus/embyBot
   ```
2. Copy and edit the environment variables file:

   ```bash
   cp .env.example .env
   vim .env
   ```
3. Sync dependency environment

   ```bash
   uv sync
   ```
4. Run the bot:

   ```bash
   uv run app.py
   ```

## ⛏ Code Quality

### Unit Tests

```shell
$ Writing...
```

### Integration Tests

Continuous integration with [Sourcery-ai](https://sourcery.ai//).

### Code Standards

Use [Ruff](https://docs.astral.sh/ruff/) and [Codecov](https://codecov.io/) to maintain code quality.

## 🎀 Contribution Guide

Please refer to the [Contribution Guide](./CONTRIBUTING.md).

## 💗 Acknowledgments

- [Pyrogram](https://docs.pyrogram.org/) - Telegram API for Python
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL Toolkit and Object-Relational Mapping
- [Emby Management Bot by 小草](https://github.com/xiaocao666tzh/EmbyBot)

## 🎡 Activities

![Alt](https://repobeats.axiom.co/api/embed/079b23892e48f7b9e6be2f0cb2c66b2833eeffda.svg "Repobeats analytics image")
