import os
import psycopg

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#URL de conexión a PostgreSQL, definida en compose.yaml
DATABASE_URL = os.environ["DATABASE_URL"]


#conexión que utilizan actualmente nuestros endpoints
def get_connection():
    return psycopg.connect(DATABASE_URL)


#motor de conexión de SQLAlchemy con PostgreSQL
engine = create_engine(DATABASE_URL)


#fabrica de sesiones para trabajar con la base de datos
SessionLocal = sessionmaker(bind=engine)


#proporciona una sesión y garantiza que se cierre al terminar
def get_db():
    db = SessionLocal() #Crea una sesión para consultar la base de datos
    try:
        yield db
    finally:
        db.close()