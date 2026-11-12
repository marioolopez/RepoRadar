#librerías estándar de Python
from datetime import datetime, timezone

#FastAPI y SQLAlchemy
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

#Archivos de nuestro proyecto
from database import get_db
from modelos.proyectos import Proyecto as ProyectoDB #importamos el modelo si queremos utilizar sus atributos
from modelos.analisis import Analisis as AnalisisDB #importamos el modelo si queremos utilizar sus atributos
from modelos.vulnerabilidades import Vulnerabilidad as VulnerabilidadDB#importamos el modelo si queremos utilizar sus atributos
from servicios.analizador import analizar_repositorio


#ES COMO UNA RUTA PRINCIPAL QUE TU LE DAS A ESTE FICHERO ENTERO
router = APIRouter(prefix="/proyectos", tags=["Análisis"])


#crear un análisis para un proyecto existente
@router.post("/{proyecto_id}/analisis", status_code=201)
def crear_analisis(
    proyecto_id: int, #id del proyecto que queremos analizar
    db: Session = Depends(get_db) #una sesion que abrimos para comunicarnos con PostgreSQL
):

    #comprobamos que el proyecto existe
    proyecto = db.get(ProyectoDB, proyecto_id)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    #creamos un análisis asociado al proyecto
    nuevo_analisis = AnalisisDB(proyecto_id=proyecto_id)

    #guardamos el análisis en PostgreSQL
    db.add(nuevo_analisis)
    db.commit()
    #recuperamos los valores generados por PostgreSQL
    db.refresh(nuevo_analisis)

    return nuevo_analisis











#ejecutar un análisis que ya existe
@router.post("/analisis/{analisis_id}/ejecutar")
def ejecutar_analisis(
    analisis_id: int,
    db: Session = Depends(get_db)
):

    #buscamos el análisis en PostgreSQL
    analisis = db.get(AnalisisDB, analisis_id)

    if analisis is None:
        raise HTTPException(
            status_code=404,
            detail="Análisis no encontrado"
        )

    #solo permitimos ejecutar análisis pendientes
    if analisis.estado != "pendiente":
        raise HTTPException(
            status_code=409,
            detail="El análisis ya ha sido ejecutado o iniciado"
        )

    #buscamos su proyecto
    proyecto = db.get(ProyectoDB, analisis.proyecto_id)

    if proyecto is None:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )

    #registramos que el análisis está ejecutándose
    analisis.estado = "ejecutando"
    db.commit()

    try:
        #solicitamos el análisis a Semgrep, Gitleaks y Trivy
        resultado = analizar_repositorio(proyecto.url_repositorio)

        #guardamos cada vulnerabilidad encontrada
        for hallazgo in resultado["vulnerabilidades"]:

            nueva_vulnerabilidad = VulnerabilidadDB(
                analisis_id=analisis.id,
                herramienta=hallazgo["herramienta"],
                regla=hallazgo["regla"],
                archivo=hallazgo["archivo"],
                linea=hallazgo["linea"],
                mensaje=hallazgo["mensaje"],
                severidad=hallazgo["severidad"]
            )

            db.add(nueva_vulnerabilidad)

        #cambiamos el estado y registramos la fecha final
        analisis.estado = "completado"
        analisis.fecha_fin = (
            datetime.now(timezone.utc).replace(tzinfo=None)
        )

        #guardamos el análisis y sus vulnerabilidades juntos
        db.commit()

    except Exception:
        #descartamos cambios pendientes de la transacción
        db.rollback()

        #registramos que el análisis ha fallado
        analisis.estado = "fallido"
        analisis.fecha_fin = (
            datetime.now(timezone.utc).replace(tzinfo=None)
        )

        db.commit()

        raise HTTPException(
            status_code=500,
            detail="Error al ejecutar el análisis"
        )

    # Recuperamos los valores definitivos de PostgreSQL
    db.refresh(analisis)

    return {
        "analisis_id": analisis.id,
        "estado": analisis.estado,
        "resultado": resultado
    }











#consultar las vulnerabilidades de un análisis
@router.get("/analisis/{analisis_id}/vulnerabilidades")
def obtener_vulnerabilidades(
    analisis_id: int,
    db: Session = Depends(get_db)
):
    #comprobamos que el análisis existe
    analisis = db.get(AnalisisDB, analisis_id)

    if analisis is None:
        raise HTTPException(
            status_code=404,
            detail="Análisis no encontrado"
        )

    #buscamos todas las vulnerabilidades de ese análisis
    vulnerabilidades = (
        db.query(VulnerabilidadDB)
        .filter(VulnerabilidadDB.analisis_id == analisis_id)
        .all()
    )

    #devolvemos los resultados
    return {
        "analisis_id": analisis_id,
        "total_vulnerabilidades": len(vulnerabilidades),
        "vulnerabilidades": vulnerabilidades
    }









#obtener los análisis de un proyecto
@router.get("/{proyecto_id}/analisis")
def listar_analisis(
    proyecto_id: int,
    db: Session = Depends(get_db)
):
    #comprobamos que el proyecto existe
    proyecto = db.get(ProyectoDB, proyecto_id)

    if proyecto is None:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )

    #recuperamos todos sus análisis
    analisis = (
        db.query(AnalisisDB)
        .filter(AnalisisDB.proyecto_id == proyecto_id)
        .order_by(AnalisisDB.id.desc())
        .all()
    )

    return analisis