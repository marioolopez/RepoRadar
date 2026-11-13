#descargamos versiones concretas para que la instalación sea reproducible.
#esta configuración está preparada para Linux AMD64.

FROM semgrep/semgrep:1.183.0

WORKDIR /scanner

#herramientas necesarias
RUN apk add --no-cache git curl tar

#instalamos Gitleaks
RUN curl -fL \
    https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz \
    -o /tmp/gitleaks.tar.gz \
    && tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks \
    && chmod +x /usr/local/bin/gitleaks \
    && rm /tmp/gitleaks.tar.gz

#instalamos Trivy
RUN curl -fL \
    https://github.com/aquasecurity/trivy/releases/download/v0.76.2/trivy_0.76.2_Linux-64bit.tar.gz \
    -o /tmp/trivy.tar.gz \
    && tar -xzf /tmp/trivy.tar.gz -C /usr/local/bin trivy \
    && chmod +x /usr/local/bin/trivy \
    && rm /tmp/trivy.tar.gz

#entorno Python de la API interna
RUN python3 -m venv /opt/scanner-venv

RUN /opt/scanner-venv/bin/pip install --no-cache-dir fastapi uvicorn

COPY security/scanner/api.py ./api.py
COPY security/reglas/ ./reglas/

EXPOSE 8001

CMD ["/opt/scanner-venv/bin/uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
