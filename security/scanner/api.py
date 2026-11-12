import json
import os
import re
import subprocess
import tempfile

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

app = FastAPI(title="RepoRadar Scanner")

PATRON_GITHUB = re.compile(
    r"^https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


class SolicitudEscaneo(BaseModel):
    url_repositorio: str

    @field_validator("url_repositorio")
    @classmethod
    def validar_url(cls, url):
        if not PATRON_GITHUB.fullmatch(url):
            raise ValueError("Solo se permiten repositorios HTTPS de github.com")
        return url


@app.get("/health")
def health():
    return {"status": "ok"}





#Ejecuta una herramienta sin utilizar shell=True
def ejecutar_comando(comando, timeout=120, entorno=None):

    try:
        return subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=entorno
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Una herramienta ha superado su tiempo máximo"
        )


def ruta_relativa(ruta, directorio):
    """Evita guardar rutas temporales absolutas."""
    ruta = str(ruta)

    if os.path.isabs(ruta):
        return os.path.relpath(ruta, directorio)

    return ruta





#Analisis estático del codigo Python
def analizar_semgrep(directorio):

    proceso = ejecutar_comando([
        "semgrep",
        "scan",
        "--config", "/scanner/reglas/seguridad-python.yaml",
        "--json",
        "--metrics=off",
        "--no-git-ignore",
        directorio
    ], timeout=120)

    if proceso.returncode != 0:
        raise HTTPException(500, "Semgrep no pudo completar el análisis")

    datos = json.loads(proceso.stdout)
    hallazgos = []

    for item in datos.get("results", []):
        hallazgos.append({
            "herramienta": "semgrep",
            "regla": item["check_id"],
            "archivo": ruta_relativa(item["path"], directorio),
            "linea": item["start"]["line"],
            "mensaje": item["extra"]["message"],
            "severidad": item["extra"]["severity"]
        })

    return hallazgos






#Detecta posibles secretos sin devolver sus valores
def analizar_gitleaks(directorio, carpeta_temporal):

    informe = os.path.join(carpeta_temporal, "gitleaks.json")

    proceso = ejecutar_comando([
        "gitleaks",
        "dir",
        directorio,
        "--report-format", "json",
        "--report-path", informe,
        "--redact=100",
        "--exit-code", "0"
    ], timeout=120)

    if proceso.returncode != 0:
        raise HTTPException(500, "Gitleaks no pudo completar el análisis")

    if not os.path.exists(informe):
        return []

    with open(informe, encoding="utf-8") as archivo:
        datos = json.load(archivo)

    hallazgos = []

    for item in datos or []:
        hallazgos.append({
            "herramienta": "gitleaks",
            "regla": item.get("RuleID", "secreto-detectado"),
            "archivo": ruta_relativa(item.get("File", ""), directorio),
            "linea": item.get("StartLine", 0),
            "mensaje": "Posible secreto expuesto: " +
                       item.get("Description", "Secreto detectado"),
            "severidad": "ERROR"
        })

    return hallazgos







#Detecta CVEs en dependencias del repositorio
def analizar_trivy(directorio, carpeta_temporal):

    informe = os.path.join(carpeta_temporal, "trivy.json")

    proceso = ejecutar_comando([
        "trivy",
        "fs",
        "--scanners", "vuln",
        "--format", "json",
        "--output", informe,
        "--exit-code", "0",
        "--timeout", "5m",
        directorio
    ], timeout=360)

    if proceso.returncode != 0:
        raise HTTPException(500, "Trivy no pudo completar el análisis")

    with open(informe, encoding="utf-8") as archivo:
        datos = json.load(archivo)

    hallazgos = []

    for resultado in datos.get("Results", []):
        archivo = ruta_relativa(
            resultado.get("Target", ""),
            directorio
        )

        for item in resultado.get("Vulnerabilities", []) or []:
            paquete = item.get("PkgName", "desconocido")
            version = item.get("InstalledVersion", "desconocida")
            cve = item.get("VulnerabilityID", "CVE-desconocido")

            hallazgos.append({
                "herramienta": "trivy",
                "regla": cve,
                "archivo": archivo,
                "linea": 0,
                "mensaje": f"{paquete} {version}: {cve}",
                "severidad": item.get("Severity", "UNKNOWN")
            })

    return hallazgos






@app.post("/scan")
def ejecutar_escaneo(solicitud: SolicitudEscaneo):

    #creamos una carpeta temporal que se elimina al terminar
    with tempfile.TemporaryDirectory(prefix="sentinelforge_") as carpeta:

        directorio = os.path.join(carpeta, "codigo")

        #configuramos Git para evitar solicitudes interactivas
        entorno = os.environ.copy()
        entorno["GIT_TERMINAL_PROMPT"] = "0"
        entorno["GIT_CONFIG_NOSYSTEM"] = "1"
        entorno["GIT_CONFIG_GLOBAL"] = "/dev/null"
        entorno["GIT_LFS_SKIP_SMUDGE"] = "1"

        #1-DESCARGAR EL REPOSITORIO
        #no materializamos sus archivos todavía
        clonacion = ejecutar_comando([
            "git",
            "-c", "core.hooksPath=/dev/null",
            "clone",
            "--depth", "1",
            "--single-branch",
            "--no-tags",
            "--no-checkout",
            solicitud.url_repositorio,
            directorio
        ], timeout=60, entorno=entorno)

        if clonacion.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail="No se pudo descargar el repositorio"
            )

        #2-COMPROBAR EL TAMAÑO DECLARADO POR GIT
        inspeccion = ejecutar_comando([
            "git", "-C", directorio,
            "ls-tree", "-r", "-l", "HEAD"
        ], timeout=15, entorno=entorno)

        if inspeccion.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail="No se pudo inspeccionar el repositorio"
            )

        total_bytes = 0
        numero_entradas = 0

        for linea in inspeccion.stdout.splitlines():
            partes = linea.split(None, 4)

            if len(partes) == 5 and partes[1] == "blob":
                numero_entradas += 1

                if partes[3].isdigit():
                    total_bytes += int(partes[3])

                # Comprobamos los límites antes del checkout
                if numero_entradas > 5000:
                    raise HTTPException(
                        status_code=413,
                        detail="El repositorio supera los 5000 archivos"
                    )

                if total_bytes > 20 * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail="El repositorio supera los 20 MB"
                    )

        #3-PREPARAR LOS ARCHIVOS DEL REPOSITORIO
        checkout = ejecutar_comando([
            "git", "-C", directorio,
            "-c", "core.hooksPath=/dev/null",
            "checkout", "--force", "HEAD"
        ], timeout=30, entorno=entorno)

        if checkout.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail="No se pudo preparar el repositorio"
            )

        #4-COMPROBAR LOS ARCHIVOS REALES
        #esta comprobación complementa la realizada con Git.
        numero_archivos = 0
        tamano_total = 0

        for raiz, carpetas, archivos in os.walk(
            directorio,
            followlinks=False
        ):

            #excluimos .git y los directorios que son enlaces simbólicos
            carpetas[:] = [
                nombre for nombre in carpetas
                if nombre != ".git"
                and not os.path.islink(os.path.join(raiz, nombre))
            ]

            for nombre in archivos:
                ruta = os.path.join(raiz, nombre)

                #no seguimos enlaces simbólicos
                if os.path.islink(ruta):
                    continue

                numero_archivos += 1
                tamano_total += os.path.getsize(ruta)

                if numero_archivos > 5000:
                    raise HTTPException(
                        status_code=413,
                        detail="El repositorio supera los 5000 archivos"
                    )

                if tamano_total > 20 * 1024 * 1024:
                    raise HTTPException(
                        status_code=413,
                        detail="El repositorio supera los 20 MB de archivos"
                    )

        #5-EJECUTAR LOS TRES MOTORES DE SEGURIDAD
        semgrep = analizar_semgrep(directorio)
        gitleaks = analizar_gitleaks(directorio, carpeta)
        trivy = analizar_trivy(directorio, carpeta)

        #unificamos los hallazgos de los tres motores
        vulnerabilidades = semgrep + gitleaks + trivy

        #6-DEVOLVER LOS RESULTADOS A FASTAPI
        return {
            "estado": "completado",
            "total_vulnerabilidades": len(vulnerabilidades),
            "resumen": {
                "semgrep": len(semgrep),
                "gitleaks": len(gitleaks),
                "trivy": len(trivy)
            },
            "vulnerabilidades": vulnerabilidades
        }
