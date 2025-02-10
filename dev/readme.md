# 开发环境启动指引

1. 原地复制 .env.example 为 .env
2. 联系 @BotFather 创建一个bot，token 填写到 .env 中的  BOT_TOKEN
3. https://my.telegram.org/ 创建API，填写到 .env 中的 API_ID 和 API_HASH
4. 创建一个群组，将ID填写到 .env 中的 TELEGRAM_GROUP_ID
5.  .env 中的 ADMIN_LIST 填写自己的 TG ID
6. 在项目根目录，执行 bash dev/up.sh
7. 进入 http://127.0.0.1:8096 ，完成emby初始化。创建API Token，填写到 .env 中
8. ctrl + c 终止，并重新执行 bash dev/up.sh 启动
9. 输出中应该有 “Bot 进入运行状态”