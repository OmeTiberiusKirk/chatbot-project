from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


class Base(DeclarativeBase):
    pass


class Documennt(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
