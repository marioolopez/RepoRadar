#tipos de columnas de PostgreSQL
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

#compartimos la misma clase Base que los demás modelos
from modelos.proyectos import Base


class Vulnerabilidad(Base):
    #nombre de la tabla en PostgreSQL
    __tablename__ = "vulnerabilidades"

    #ddentificador único de la vulnerabilidad
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    #análisis al que pertenece esta vulnerabilidad
    analisis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("analisis.id"),
        nullable=False
    )

    #herramienta que encuentra la vulnerabilidad
    herramienta: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="semgrep"
    )

    #regla de Semgrep que detectó el problema
    regla: Mapped[str] = mapped_column(String(200), nullable=False)

    #archivo donde se encontró
    archivo: Mapped[str] = mapped_column(Text, nullable = False)

    #línea del código donde aparece
    linea: Mapped[int] = mapped_column(Integer, nullable =False)

    #explicación del problema
    mensaje: Mapped[str] = mapped_column(Text, nullable = False)

    #gravedad del hallazgo
    severidad: Mapped[str] = mapped_column(String(20), nullable =False)
