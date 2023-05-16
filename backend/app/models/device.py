from sqlalchemy.sql.schema import Table
from backend.app.db.base_class import Base
from sqlalchemy import Column, ForeignKey, Integer, Boolean, String
from sqlalchemy.orm import relationship


device_user_link = Table(
    "device_user",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("device.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
)


class Device(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True,unique=True,nullable=False)
    mac_id = Column(String, index=True, unique=True, nullable=False)

    is_active = Column(Boolean(), default=False)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    agent_id = Column(Integer, ForeignKey("agent.id"), nullable=False)

    assigned_users = relationship(
        "User", secondary=device_user_link, back_populates="devices"
    )
