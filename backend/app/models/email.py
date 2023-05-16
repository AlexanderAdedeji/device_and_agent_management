from sqlalchemy.sql.sqltypes import JSON
from backend.app.db.base_class import Base
from sqlalchemy import Column, ForeignKey, Integer, Boolean, String


class Email(Base):
    id = Column(Integer, primary_key=True, index=True)
    delivered = Column(Boolean(), default=False)
    recipient = Column(String, nullable=False)
    template_id = Column(String, nullable=False)
    template_dict = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    extra_data = Column(String, default="")
