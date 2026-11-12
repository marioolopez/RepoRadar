FROM python:3.12-slim

WORKDIR /app

#instalamos las dependencias de Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#copiamos el código del backend
COPY backend/main.py backend/database.py ./
COPY backend/rutas/ ./rutas/
COPY backend/esquemas/ ./esquemas/
COPY backend/modelos/ ./modelos/
COPY backend/servicios/ ./servicios/

#configuración y migraciones de Alembic
COPY backend/alembic.ini ./
COPY backend/alembic/ ./alembic/

#pruebas automáticas
COPY backend/tests/ ./tests/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]