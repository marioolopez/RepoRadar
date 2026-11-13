# RepoRadar

**Plataforma web de análisis de seguridad para repositorios de GitHub.**

RepoRadar es un proyecto personal de desarrollo Backend y DevSecOps que permite registrar repositorios públicos de GitHub, ejecutar análisis de seguridad y consultar las vulnerabilidades detectadas desde un dashboard web.

La aplicación integra tres herramientas de seguridad: **Semgrep, Gitleaks y Trivy**, que permiten analizar diferentes aspectos del código y sus dependencias.

El proyecto está desarrollado utilizando Python, FastAPI, PostgreSQL, React, TypeScript y Docker.

## 1. Objetivo del proyecto

El objetivo de RepoRadar es construir una herramienta que centralice distintos análisis de seguridad en una única aplicación.

En lugar de ejecutar manualmente varias herramientas desde la terminal, RepoRadar permite:

- Registrar repositorios públicos de GitHub.
- Crear y ejecutar análisis de seguridad.
- Descargar temporalmente el código de los repositorios.
- Analizar el código mediante varios motores de seguridad.
- Guardar los hallazgos en una base de datos PostgreSQL.
- Consultar análisis anteriores.
- Filtrar vulnerabilidades por herramienta y severidad.
- Visualizar estadísticas de seguridad desde una interfaz web.

RepoRadar se ha desarrollado como un proyecto de aprendizaje práctico y portfolio, aplicando conocimientos de desarrollo backend, bases de datos, contenedores y seguridad de aplicaciones.

## 2. Tecnologías utilizadas

### Backend

| Tecnología | Función |
|---|---|
| Python 3.12 | Lenguaje principal del backend |
| FastAPI | Desarrollo de la API REST |
| Uvicorn | Servidor ASGI de la aplicación |
| Pydantic | Validación de datos |
| SQLAlchemy | ORM para gestionar la base de datos |
| Alembic | Gestión de migraciones de PostgreSQL |
| Psycopg | Conexión Python con PostgreSQL |
| HTTPX | Comunicación HTTP entre servicios |
| Pytest | Pruebas automatizadas del backend |

### Frontend

| Tecnología | Función |
|---|---|
| React | Construcción de la interfaz web |
| TypeScript | Tipado de datos y componentes |
| Vite | Entorno de desarrollo y compilación |
| CSS | Diseño del dashboard |
| Fetch API | Comunicación con FastAPI |

### Base de datos

**PostgreSQL 17**

Almacena los proyectos registrados, sus análisis de seguridad y las vulnerabilidades detectadas.

### Contenedores e infraestructura

| Tecnología | Función |
|---|---|
| Docker | Contenedorización de los servicios |
| Docker Compose | Orquestación del entorno local |
| Linux / Ubuntu WSL2 | Entorno de desarrollo |
| Git | Control de versiones |
| GitHub | Alojamiento del código fuente |
| GitHub Actions | Pipeline de integración continua |

### Herramientas de seguridad

**Semgrep — SAST**

Analiza el código fuente utilizando reglas de análisis estático.

RepoRadar incluye reglas personalizadas para detectar patrones potencialmente inseguros en Python, como:

- Uso de `eval()`.
- Uso de `exec()`.
- Ejecución de comandos mediante `subprocess` con `shell=True`.
- Deserialización mediante `pickle.load()`.

**Gitleaks — Detección de secretos**

Busca posibles credenciales, claves y tokens expuestos en los archivos del repositorio.

La integración actual analiza el directorio de trabajo descargado y no constituye una auditoría completa de todo el historial de Git.

**Trivy — Análisis de dependencias**

Analiza dependencias del repositorio e identifica vulnerabilidades conocidas, incluyendo identificadores CVE cuando existen coincidencias.

Los resultados dependen de los archivos de dependencias disponibles y de las bases de datos de vulnerabilidades utilizadas por Trivy.

## 3. Arquitectura de la aplicación

RepoRadar utiliza una arquitectura basada en varios servicios Docker conectados mediante una red interna.

```text
                   USUARIO
                      |
                      v
              REACT + TYPESCRIPT
                 Frontend
                Puerto 5173
                      |
                      v
                  FASTAPI
                  Backend
                Puerto 8000
                      |
             +--------+--------+
             |                 |
             v                 v
        POSTGRESQL       SERVICIO SCANNER
        Base de datos           |
                          +-----+-----+
                          |     |     |
                          v     v     v
                       Semgrep Gitleaks Trivy
                          |
                          v
                   Repositorio GitHub
```

El frontend permite interactuar con la aplicación y consultar resultados.

FastAPI gestiona la lógica de negocio, la creación de proyectos y los análisis.

El servicio de escaneo descarga temporalmente el repositorio solicitado y ejecuta los tres motores de seguridad.

PostgreSQL almacena el estado de los análisis y sus hallazgos.

## 4. Funcionamiento de un análisis

El proceso de análisis sigue estos pasos:

1. El usuario registra un repositorio público de GitHub desde React.
2. FastAPI almacena el proyecto en PostgreSQL.
3. El usuario solicita un nuevo análisis.
4. Se crea un registro de análisis con estado `pendiente`.
5. Al ejecutarlo, el estado pasa a `ejecutando`.
6. FastAPI envía la URL del repositorio al servicio de escaneo.
7. El servicio descarga el repositorio en un directorio temporal.
8. Se ejecutan Semgrep, Gitleaks y Trivy.
9. Los hallazgos se convierten a una estructura común.
10. FastAPI guarda las vulnerabilidades en PostgreSQL.
11. El análisis pasa a `completado`, o a `fallido` si se produce un error.
12. React permite consultar los resultados desde el dashboard.

Actualmente, la ejecución se realiza mediante una petición HTTP síncrona. La implementación de trabajos en segundo plano forma parte de las mejoras futuras.

## 5. Modelo de datos

La base de datos utiliza tres tablas principales.

### Proyectos

Tabla `proyectos`.

Contiene:

- `id`: identificador del proyecto.
- `nombre`: nombre del proyecto.
- `url_repositorio`: URL de GitHub.
- `fecha_creacion`: fecha de registro.

### Análisis

Tabla `analisis`.

Contiene:

- `id`: identificador del análisis.
- `proyecto_id`: proyecto al que pertenece.
- `estado`: pendiente, ejecutando, completado o fallido.
- `fecha_inicio`: fecha de creación del análisis.
- `fecha_fin`: fecha de finalización.

Un proyecto puede tener varios análisis.

### Vulnerabilidades

Tabla `vulnerabilidades`.

Contiene:

- `id`: identificador del hallazgo.
- `analisis_id`: análisis que detectó el problema.
- `herramienta`: Semgrep, Gitleaks o Trivy.
- `regla`: regla de seguridad o identificador CVE.
- `archivo`: archivo afectado.
- `linea`: número de línea, cuando corresponda.
- `mensaje`: descripción del hallazgo.
- `severidad`: gravedad indicada por la herramienta.

Un análisis puede almacenar múltiples vulnerabilidades.

## 6. API REST

FastAPI proporciona endpoints para gestionar proyectos y ejecutar análisis.

Algunos de los principales son:

| Método | Endpoint | Función |
|---|---|---|
| GET | `/proyectos` | Listar proyectos |
| POST | `/proyectos` | Crear proyecto |
| POST | `/proyectos/{proyecto_id}/analisis` | Crear análisis |
| GET | `/proyectos/{proyecto_id}/analisis` | Consultar historial |
| POST | `/proyectos/analisis/{analisis_id}/ejecutar` | Ejecutar análisis |
| GET | `/proyectos/analisis/{analisis_id}/vulnerabilidades` | Consultar vulnerabilidades |
| GET | `/health` | Comprobar el estado básico del backend |
| GET | `/db-health` | Comprobar la conexión con PostgreSQL |
| GET | `/proyectos/{proyecto_id}` | Consultar un proyecto |
| PUT | `/proyectos/{proyecto_id}` | Actualizar un proyecto |
| DELETE | `/proyectos/{proyecto_id}` | Eliminar un proyecto y sus registros asociados |

La documentación interactiva de la API está disponible mediante Swagger UI:

`http://localhost:8000/docs`

## 7. Dashboard web

El frontend está desarrollado con React y TypeScript.

Permite:

- Crear proyectos sin utilizar Swagger.
- Eliminar proyectos junto con sus análisis y vulnerabilidades asociados, previa confirmación.
- Seleccionar proyectos registrados.
- Ejecutar análisis de seguridad.
- Consultar resultados anteriores.
- Visualizar el número de hallazgos de Semgrep, Gitleaks y Trivy.
- Filtrar vulnerabilidades por herramienta y severidad.
- Consultar descripciones, archivos y líneas de código.
- Visualizar gráficas de distribución de vulnerabilidades.
- Consultar el historial de análisis y sus estados.

La interfaz se comunica con FastAPI a través del proxy de desarrollo configurado en Vite.

## 8. Estructura del proyecto

```text
sentinelforge/
├── backend/
│   ├── alembic/
│   ├── esquemas/
│   ├── modelos/
│   ├── rutas/
│   ├── servicios/
│   ├── tests/
│   ├── database.py
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── PanelEstadisticas.tsx
│   │   └── PanelEstadisticas.css
│   ├── package.json
│   └── vite.config.ts
├── security/
│   ├── ejemplos/
│   ├── reglas/
│   └── scanner/
│       ├── api.py
│       └── Dockerfile
├── docs/
├── infra/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── .gitignore
├── .dockerignore
├── compose.yml
└── README.md
```

*La carpeta raíz conserva su nombre técnico original por compatibilidad con el entorno de desarrollo. El nombre público del proyecto es RepoRadar.*

## 9. Instalación y ejecución local

### Requisitos

Para ejecutar RepoRadar se necesita:

- Git.
- Docker Engine con Docker Compose, o Docker Desktop.
- Acceso a Internet para descargar las imágenes y las bases de datos de seguridad.
- Recursos suficientes para ejecutar varios contenedores.

### Clonar el repositorio

```bash
git clone https://github.com/marioolopez/RepoRadar.git
cd RepoRadar
```

Sustituir `TU_USUARIO` por el propietario real del repositorio.

### Configurar las variables de entorno

Crear un archivo `.env` tomando como referencia `.env.example`.

```bash
cp .env.example .env
```

Editar `.env` para establecer las credenciales locales.

La contraseña de PostgreSQL debe coincidir con la utilizada en `DATABASE_URL`.

No subir `.env` a GitHub.

### Iniciar los servicios

```bash
docker compose up -d --build
```

### Aplicar las migraciones

En una instalación nueva:

```bash
docker compose exec backend alembic upgrade head
```

### Abrir la aplicación

Dashboard:

`http://localhost:5173`

Swagger:

`http://localhost:8000/docs`

### Detener los contenedores

```bash
docker compose down
```

No utilizar `docker compose down -v` si se desean conservar los datos del volumen PostgreSQL.

## 10. Pruebas automatizadas

RepoRadar incorpora pruebas del backend utilizando Pytest, FastAPI TestClient y SQLite en memoria.

Las pruebas permiten comprobar:

1. La creación de análisis asociados a proyectos.
2. La respuesta HTTP 404 para proyectos inexistentes.
3. La ejecución de análisis y el almacenamiento de vulnerabilidades.
4. La prevención de ejecuciones repetidas.
5. La recuperación del historial de análisis.

Las respuestas del servicio de seguridad se simulan para que las pruebas sean rápidas y no necesiten conexión a GitHub ni ejecución real de escáneres.

### Ejecutar las pruebas

```bash
docker compose exec backend python -m pytest -v tests/test_analisis.py
```

**Último resultado local verificado: 5 pruebas superadas.**

### Comprobar el frontend

```bash
docker compose exec frontend npm run build
```

## 11. Integración continua

El proyecto incluye un workflow de GitHub Actions en:

`.github/workflows/ci.yml`

El pipeline está configurado para ejecutarse en eventos `push`, `pull_request` y de forma manual.

Realiza dos trabajos:

**Backend:** instala Python y las dependencias, y ejecuta las pruebas de Pytest.

**Frontend:** instala Node.js, ejecuta `npm ci` y comprueba la compilación con `npm run build`.

El proyecto cuenta con un pipeline de integración continua configurado mediante GitHub Actions.

Cada vez que se realiza un `push` o se abre una Pull Request, GitHub ejecuta automáticamente dos trabajos:

- **Pruebas del backend:** instalación de dependencias de Python y ejecución de Pytest.
- **Compilación del frontend:** instalación de dependencias de Node.js y compilación de React y TypeScript.

Ambos trabajos han sido ejecutados y verificados correctamente en GitHub Actions.

## 12. Seguridad y limitaciones actuales

RepoRadar es un proyecto educativo y de portfolio, no una plataforma preparada para recibir análisis arbitrarios de usuarios desconocidos en producción.

La implementación actual incluye algunas medidas de protección:

- Validación básica de URLs HTTPS de GitHub.
- Clonación superficial de repositorios.
- Ejecución de comandos sin `shell=True`.
- Directorios temporales para el código descargado.
- Tiempos máximos de ejecución.
- Comprobaciones básicas del tamaño y número de archivos.
- Separación entre backend y servicio de escaneo.
- Variables de entorno para las credenciales.
- Puertos de desarrollo vinculados a la interfaz local.

### Limitaciones conocidas

- El escaneo todavía no se ejecuta mediante una cola de trabajos en segundo plano.
- La plataforma no dispone aún de autenticación ni autorización.
- No cuenta con aislamiento de seguridad suficiente para procesar repositorios arbitrarios no confiables como servicio público.
- Los límites actuales no impiden completamente el consumo excesivo de recursos durante la clonación.
- Gitleaks analiza los archivos descargados, no el historial Git completo.
- La cobertura SAST depende de las reglas Semgrep configuradas.
- Las severidades de los tres motores todavía no están completamente normalizadas.
- Los resultados almacenados no incluyen todavía toda la información de trazabilidad que sería deseable en producción.

**No ejecutar ni desplegar el escáner como servicio público sin aplicar medidas adicionales de aislamiento y seguridad.**

El código de `security/ejemplos/` contiene patrones intencionadamente inseguros para comprobar las reglas de Semgrep. No está destinado a ejecutarse.

## 13. Próximas mejoras

Las siguientes funcionalidades forman parte de la hoja de ruta:

- Ejecución de análisis en segundo plano.
- Autenticación y autorización de usuarios.
- Aislamiento reforzado de los escáneres.
- Límites de CPU, memoria, disco y procesos.
- Mejor normalización de severidades.
- Ampliación de reglas de seguridad.
- Pruebas de integración con los motores reales.
- Historial más detallado y trazabilidad por commit.
- Mejoras en gestión de errores y observabilidad.
- Auditoría de dependencias y endurecimiento de contenedores.
- Despliegue seguro de la aplicación.

## 14. Conocimientos aplicados

Durante el desarrollo de RepoRadar se han aplicado conocimientos de distintas áreas.

**Desarrollo backend**

Diseño de APIs REST, validación de datos, ORM, lógica de negocio, gestión de errores y persistencia relacional.

**Frontend**

Componentes React, estados, efectos, TypeScript, peticiones HTTP, formularios y visualización de datos.

**Bases de datos**

PostgreSQL, relaciones mediante claves foráneas, consultas SQL y migraciones con Alembic.

**DevOps**

Docker, Docker Compose, redes entre contenedores, variables de entorno, Git y automatización CI.

**DevSecOps y AppSec**

Análisis estático de código, detección de secretos, análisis de dependencias, gestión de hallazgos y prácticas básicas de seguridad.

**Testing**

Pruebas con Pytest, simulación de dependencias, FastAPI TestClient y bases de datos temporales.

## 15. Estado del proyecto

**Estado actual: MVP funcional en desarrollo.**

El proyecto permite analizar repositorios públicos de GitHub desde una interfaz web, ejecutar tres herramientas de seguridad y consultar los resultados almacenados en PostgreSQL.

La aplicación se encuentra en evolución y no debe considerarse una solución de seguridad lista para producción.

---

**RepoRadar — Proyecto personal de Backend y DevSecOps.**
