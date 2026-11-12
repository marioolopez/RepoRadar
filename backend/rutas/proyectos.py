from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from esquemas.proyectos import Proyecto
from modelos.proyectos import Proyecto as ProyectoDB

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from modelos.analisis import Analisis as AnalisisDB
from modelos.vulnerabilidades import Vulnerabilidad as VulnerabilidadDB


#ruta enlazada desde la carpeta rutas/proyectos (que es donde tienes los endpoints)
router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


#crear un proyecto
@router.post("")
def crear_proyecto(
    proyecto: Proyecto, #datos que envia el usuario
    db: Session = Depends(get_db) #sesion que proporciona FastApi (COSA QUE ANTES HACIAMOS ASI "with get_connection() as conexion:" --> ahora ya no, nos proporciona una sesion automaticamente)
):

    #creo objeto que representa el nuevo registro
    nuevo_proyecto = ProyectoDB(nombre=proyecto.nombre,url_repositorio=proyecto.url_repositorio)

    #añado el proyecto a la sesion
    db.add(nuevo_proyecto)
    #confirmo el cambio
    db.commit()
    #recupero valores generados por PostgreSQL, como el ID
    db.refresh(nuevo_proyecto)
    #devolvemos el proyecto creado
    return nuevo_proyecto





#listar todos los proyectos utilizando SQLAlchemy
@router.get("")
def listar_proyectos(db: Session = Depends(get_db)):
    #construimos la consulta y ordenamos los proyectos por ID
    consulta = select(ProyectoDB).order_by(ProyectoDB.id)
    #ejecuto consulta y obtengo los proyectos
    proyectos = db.scalars(consulta).all()
    #devolvemos los proyectos encontrados
    return proyectos





#consultar proyecto por su ID utilizando SQLAlchemy
@router.get("/{proyecto_id}")
def obtener_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db)
):

    #buscamos el proyecto mediante su clave primaria
    proyecto = db.get(ProyectoDB, proyecto_id)

    #si no existe, devolvemos un error HTTP 404
    if proyecto is None:
        raise HTTPException(status_code=404,detail="Proyecto no encontrado")

    #devolvemos el proyecto encontrado
    return proyecto





#actualizar proyecto utilizando SQLAlchemy
@router.put("/{proyecto_id}")
def actualizar_proyecto(
    proyecto_id: int,
    proyecto: Proyecto,
    db: Session = Depends(get_db)
):

    #buscamos el proyecto por su ID
    proyecto_db = db.get(ProyectoDB, proyecto_id)

    #comprobamos si existe
    if proyecto_db is None:
        raise HTTPException(status_code=404,detail="Proyecto no encontrado")

    #modificamos los valores del proyecto
    proyecto_db.nombre = proyecto.nombre
    proyecto_db.url_repositorio = proyecto.url_repositorio

    #guardamos los cambios en PostgreSQL
    db.commit()

    #actualizamos el objeto con los datos de PostgreSQL
    db.refresh(proyecto_db)

    return proyecto_db






#eliminar proyecto y todos sus datos asociados
@router.delete("/{proyecto_id}")
def eliminar_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db)
):

    #buscamos el proyecto
    proyecto_db = db.get(ProyectoDB, proyecto_id)

    if proyecto_db is None:
        raise HTTPException(status_code=404,detail="Proyecto no encontrado")

    #evitamos borrar proyectos que tienen análisis ejecutándose
    analisis_activo = db.scalar(
        select(AnalisisDB.id)
        .where(
            AnalisisDB.proyecto_id == proyecto_id,
            AnalisisDB.estado == "ejecutando"
        )
        .limit(1)
    )

    if analisis_activo is not None:

        raise HTTPException(status_code=409,detail="No se puede eliminar un proyecto con análisis en ejecución")

    try:
        #identificamos los análisis asociados al proyecto
        ids_analisis = select(AnalisisDB.id).where(
            AnalisisDB.proyecto_id == proyecto_id
        )

        #1-Borramos las vulnerabilidades de esos análisis
        db.execute(
            delete(VulnerabilidadDB).where(
                VulnerabilidadDB.analisis_id.in_(ids_analisis)
            )
        )

        #2-Borramos los análisis
        db.execute(
            delete(AnalisisDB).where(
                AnalisisDB.proyecto_id == proyecto_id
            )
        )

        #3-Borramos el proyecto
        db.delete(proyecto_db)
        #4-Confirmamos todas las eliminaciones juntas
        db.commit()

    except SQLAlchemyError:
        #si algo falla, deshacemos la transacción
        db.rollback()

        raise HTTPException(status_code=500,detail="No se pudo eliminar el proyecto")

    return {"mensaje": "Proyecto eliminado correctamente","proyecto_id": proyecto_id}



# Depends(get_db) --> FastAPI obtiene una sesión de PostgreSQL
# db: Session --> Indica que db es una sesión SQLAlchemy
# select(ProyectoDB) --> Prepara una consulta a la tabla proyectos
# .order_by(ProyectoDB.id) --> Ordena los resultados por ID
# db.scalars(consulta).all() --> Ejecuta la consulta y obtiene todos los proyectos
# return proyectos --> FastAPI convierte los resultados en JSON


#Migramos todo el CRUD a SQLAlchemy
# Listar --> db.scalars(select(ProyectoDB)).all()
# Crear --> db.add() y db.commit()
# Buscar por ID --> db.get()
# Actualizar --> Modificar atributos y db.commit()
# Eliminar --> db.delete() y db.commit()
