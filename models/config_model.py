import logging
from py_tools.connections.db.mysql import DBManager
from py_tools.connections.db.mysql.orm_model import BaseOrmTableWithTS
from sqlalchemy import Integer, BigInteger
from sqlalchemy.orm import mapped_column, Mapped

logger = logging.getLogger(__name__)

class Config(BaseOrmTableWithTS):
    __tablename__ = 'config'

    total_register_user: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    register_public_user: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    register_public_time: Mapped[int] = mapped_column(BigInteger, nullable=True)


class ConfigOrm(DBManager):
    orm_table = Config

logger.info("Config model initialized")