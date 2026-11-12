import os
import httpx


def analizar_repositorio(url_repositorio: str):
    """Solicita el análisis de un repositorio a los tres motores."""

    scanner_url = os.getenv(
        "SCANNER_URL",
        "http://semgrep:8001"
    )

    respuesta = httpx.post(
        f"{scanner_url}/scan",
        json={
            "url_repositorio": url_repositorio
        },
        timeout=750.0
    )

    respuesta.raise_for_status()
    resultado = respuesta.json()

    return {
        "repositorio": url_repositorio,
        "objetivo_analizado": "repositorio_github",
        "estado": resultado["estado"],
        "total_vulnerabilidades": resultado["total_vulnerabilidades"],
        "resumen": resultado["resumen"],
        "vulnerabilidades": resultado["vulnerabilidades"]
    }