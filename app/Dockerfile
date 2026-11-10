#--- Etape 1 : Création et instalation du docker, on garde la configuration complète, utile à la construction.
FROM python:3.12-slim AS construction
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# --- Etape 2 : Après la completion de l'instalation on ne garde que les éléments nécessaires pour alléger la configuration 
FROM python:3.12-slim

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin colis \
 && mkdir /donnees \
 && chown 10001:10001 /donnees

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
