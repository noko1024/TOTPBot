import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime

from db.base_class import Base

class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, autoincrement=True)

    role_id = Column(Integer, nullable=False)

    guild_id = Column(String, ForeignKey('guild.guild_id'), nullable=False)
    guild = relationship("Guild", back_populates="roles")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=sqlalchemy.func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now()
    )