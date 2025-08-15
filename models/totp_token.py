import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime

from db.base_class import Base


class TOTPToken(Base):
    __tablename__ = 'totp_token'

    id = Column(Integer, primary_key=True, autoincrement=True)
    totp_token = Column(String, nullable=False)

    guild_id = Column(String, ForeignKey('guild.guild_id'), nullable=False)
    guild = relationship("Guild", back_populates="totp_tokens")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=sqlalchemy.func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now()
    )