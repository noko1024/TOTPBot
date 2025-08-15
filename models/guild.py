import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime

from db.base_class import Base


class Guild(Base):
    __tablename__ = 'guild'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    guild_id = Column(String, nullable=False, unique=True)
    totp_token = Column(String, nullable=False)

    roles = relationship("Role", back_populates="guild")
    totp_tokens = relationship("TOTPToken", back_populates="guild")
    totp_logs = relationship("TOTPlog", back_populates="guild")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=sqlalchemy.func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now()
    )