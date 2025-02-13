import logging

from bot import BotClient
from bot.command.admin_command import AdminCommandHandler
from bot.command.event_command import EventHandler
from bot.command.user_command import UserCommandHandler
from bot.command_router import setup_command_routes
from services import UserService

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, bot_client: BotClient, user_service: UserService):
        self.bot_client = bot_client
        self.user_service = user_service
        self.code_to_message_id = {}
        self.user_command_handler = UserCommandHandler(bot_client,
                                                       user_service)
        self.admin_command_handler = AdminCommandHandler(bot_client,
                                                         user_service)
        self.event_handler = EventHandler(bot_client, user_service)
        setup_command_routes(bot_client, self.user_command_handler,
                             self.admin_command_handler, self.event_handler)
        logger.info("CommandHandler initialized")
