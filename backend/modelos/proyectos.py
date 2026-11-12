from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


#clase base para los modelos SQLAlchemy
class Base(DeclarativeBase):
    pass


#representación de la tabla proyectos de PostgreSQL
class Proyecto(Base):

    __tablename__ = "proyectos"

    #identificador generado automáticamente por PostgreSQL
    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement = True)

    #nombre del proyecto
    nombre: Mapped[str] = mapped_column(String(100), nullable = False)

    #URL del repositorio
    url_repositorio: Mapped[str] = mapped_column(Text, nullable = False)

    #nullable=True refleja cómo se creó originalmente la tabla PostgreSQL
    fecha_creacion: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=True)