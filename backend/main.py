from fastapi import FastAPI
from database import get_connection
from rutas.proyectos import router as proyectos_router
from rutas.analisis import router as analisis_router

#para inicializar
app = FastAPI(title="RepoRadar API")


#endpoint de prueba
@app.get("/")
def home():
    return {"message": "Bienvenido a SentinelForge API"}


#endpoint de prueba
@app.get("/health")
def health():
    return {"status": "ok"}


#endpoint de prueba
@app.get("/db-health")
def db_health():
    with get_connection() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT 1")
            resultado = cursor.fetchone()

    return {"database": "connected" if resultado[0] == 1 else "error"}



#registrar las rutas de proyectos
app.include_router(proyectos_router)
app.include_router(analisis_router)