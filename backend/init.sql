-- 创建数据库
CREATE DATABASE IF NOT EXISTS emby_bot_db;

-- 切换到 root 用户（如果有需要）
USE mysql;

-- 为新用户 "embyplus" 授予权限
CREATE USER IF NOT EXISTS 'embyplus'@'%' IDENTIFIED BY 'embyplus';
GRANT ALL PRIVILEGES ON *.* TO 'embyplus'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 返回到默认数据库
USE emby_bot_db;

