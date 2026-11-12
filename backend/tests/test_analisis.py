#pruebas automáticas para SentinelForge
#no utilizan PostgreSQL real ni ejecutan Semgrep.

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
from modelos.proyectos import Base
from modelos.proyectos import Proyecto as ProyectoDB
from modelos.analisis import Analisis as AnalisisDB
from modelos.vulnerabilidades import Vulnerabilidad as VulnerabilidadDB


#Crea una base de datos SQLite temporal para cada prueba. Al terminar, elimina las tablas y libera los recursos.
@pytest.fixture
def entorno_prueba():

    #staticPool mantiene la misma base SQLite en memoria
    #para las peticiones que realiza TestClient.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=engine)

    SessionPrueba = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    db = SessionPrueba()


    #sustituimos la conexión PostgreSQL por la de pruebas.
    def obtener_db_prueba():
        yield db

    app.dependency_overrides[get_db] = obtener_db_prueba

    try:
        with TestClient(app) as cliente:
            yield cliente, db
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()




#Inserta un proyecto de ejemplo en SQLite
def crear_proyecto_prueba(db):

    proyecto = ProyectoDB(
        nombre="Proyecto de pruebas",
        url_repositorio="https://github.com/psf/requests"
    )

    db.add(proyecto)
    db.commit()
    db.refresh(proyecto)

    return proyecto




#Un proyecto existente debe aceptar nuevos análisis
def test_crear_analisis(entorno_prueba):

    cliente, db = entorno_prueba
    proyecto = crear_proyecto_prueba(db)

    respuesta = cliente.post(
        f"/proyectos/{proyecto.id}/analisis"
    )

    assert respuesta.status_code == 201

    datos = respuesta.json()

    assert datos["proyecto_id"] == proyecto.id
    assert datos["estado"] == "pendiente"
    assert isinstance(datos["id"], int)



#Crear un análisis para un proyecto inexistente debe fallar
def test_proyecto_inexistente(entorno_prueba):

    cliente, db = entorno_prueba

    respuesta = cliente.post(
        "/proyectos/99999/analisis"
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Proyecto no encontrado"



#Simulamos la respuesta del escáner y comprobamos. que el backend almacena el hallazgo.
def test_ejecutar_y_guardar_vulnerabilidades(
    entorno_prueba,
    monkeypatch
):

    cliente, db = entorno_prueba
    proyecto = crear_proyecto_prueba(db)

    #creamos el análisis desde la API
    creacion = cliente.post(
        f"/proyectos/{proyecto.id}/analisis"
    )

    assert creacion.status_code == 201

    analisis_id = creacion.json()["id"]




    #respuesta simulada: no ejecuta Semgrep real
    def escaner_simulado(url_repositorio):
        return {
            "repositorio": url_repositorio,
            "estado": "completado",
            "total_vulnerabilidades": 1,
            "vulnerabilidades": [
                {
                    "herramienta": "semgrep",
                    "regla": "python-eval-peligroso",
                    "archivo": "codigo_inseguro.py",
                    "linea": 10,
                    "mensaje": "Uso peligroso de eval()",
                    "severidad": "ERROR"
                }
            ]
        }

    #cambiamos temporalmente el escáner real
    #por nuestra función simulada.
    monkeypatch.setattr(
        "rutas.analisis.analizar_repositorio",
        escaner_simulado
    )

    respuesta = cliente.post(
        f"/proyectos/analisis/{analisis_id}/ejecutar"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "completado"

    #comprobamos el estado en la base de datos
    db.expire_all()

    analisis = db.get(AnalisisDB, analisis_id)

    assert analisis is not None
    assert analisis.estado == "completado"

    #comprobamos que se guardó el hallazgo
    guardadas = (
        db.query(VulnerabilidadDB)
        .filter(VulnerabilidadDB.analisis_id == analisis_id)
        .all()
    )

    assert len(guardadas) == 1
    assert guardadas[0].herramienta == "semgrep"
    assert guardadas[0].regla == "python-eval-peligroso"
    assert guardadas[0].linea == 10

    #consultamos también el endpoint GET
    consulta = cliente.get(
        f"/proyectos/analisis/{analisis_id}/vulnerabilidades"
    )

    assert consulta.status_code == 200
    assert consulta.json()["total_vulnerabilidades"] == 1




#Un análisis ya completado debe devolver 409
def test_no_ejecutar_analisis_completado(entorno_prueba):

    cliente, db = entorno_prueba
    proyecto = crear_proyecto_prueba(db)

    analisis = AnalisisDB(
        proyecto_id=proyecto.id,
        estado="completado"
    )

    db.add(analisis)
    db.commit()
    db.refresh(analisis)

    respuesta = cliente.post(
        f"/proyectos/analisis/{analisis.id}/ejecutar"
    )

    assert respuesta.status_code == 409




#El historial debe mostrar los análisis del proyecto
def test_listar_analisis_de_un_proyecto(entorno_prueba):

    cliente, db = entorno_prueba
    proyecto = crear_proyecto_prueba(db)

    # Creamos dos análisis
    for _ in range(2):
        respuesta = cliente.post(
            f"/proyectos/{proyecto.id}/analisis"
        )
        assert respuesta.status_code == 201

    #consultamos su historial
    respuesta = cliente.get(
        f"/proyectos/{proyecto.id}/analisis"
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert len(datos) == 2
    assert all(
        item["proyecto_id"] == proyecto.id
        for item in datos
    )
