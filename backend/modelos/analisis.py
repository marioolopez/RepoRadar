# Importamos los tipos de columnas de SQLAlchemy
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

#reutilizamos la misma clase Base del modelo proyectos
from modelos.proyectos import Base


#modelo que representa la tabla "analisis"
class Analisis(Base):

    __tablename__ = "analisis"

    #identificador único de cada análisis
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    #proyecto al que pertenece el análisis
    proyecto_id: Mapped[int] = mapped_column(Integer, ForeignKey("proyectos.id"), nullable=False)

    #estado inicial del análisis
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pendiente")

    #fecha en que se registra el análisis
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)

    #fecha de finalización, inicialmente vacía
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)