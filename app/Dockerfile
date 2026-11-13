# --- Etape 1 : construction du venv (les outils de build ne sont pas livres)
FROM python:3.12-alpine AS construction
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
# pip sert a installer les dependances, puis il est retire du venv livre
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && pip uninstall -y pip
 
# --- Etape 2 : image finale minimale, non root
FROM python:3.12-alpine
# correctifs systeme du jour, utilisateur 10001 sans shell, dossier de donnees,
# puis retrait des outils de packaging inutiles a l'execution
RUN apk upgrade --no-cache \
 && adduser -D -H -u 10001 -s /sbin/nologin colis \
 && mkdir /donnees && chown 10001:10001 /donnees \
 && python -m pip uninstall -y pip setuptools wheel
 
COPY --from=construction /opt/venv /opt/venv
 
ENV PATH=/opt/venv/bin:$PATH \
    COLIS_DONNEES=/donnees
WORKDIR /app
COPY . /app
 
USER 10001
 
EXPOSE 8080
 
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/sante', timeout=2)"]
 
CMD ["python", "app.py"]
