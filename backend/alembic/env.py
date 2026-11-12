from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


#importamos el modelo y su clase Base
from modelos.proyectos import Base, Proyecto
target_metadata = Base.metadata

#importamos la Base compartida por nuestros modelos
from modelos.proyectos import Base, Proyecto

#importamos el nuevo modelo para registrarlo en Base.metadata
from modelos.analisis import Analisis

#importamos el modelo de vulnerabilidades
from modelos.vulnerabilidades import Vulnerabilidad

#alembic utiliza estos metadatos para detectar cambios
target_metadata = Base.metadata


from database import DATABASE_URL #obtenemos la URL de PostgreSQL desde la variable de entorno
def run_migrations_offline() -> None:

    url = DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()




from database import engine
def run_migrations_online() -> None:

    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
