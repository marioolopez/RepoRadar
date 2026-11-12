from pydantic import BaseModel


#para crear un proyecto, necesito un nombre y una URL, ambos como texto
class Proyecto(BaseModel):
    nombre: str
    url_repositorio: str