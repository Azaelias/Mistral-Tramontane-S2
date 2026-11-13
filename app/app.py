"""Suivi Colis : le portail de suivi des colis de Mistral Logistique (fictive).

Variables d'environnement :
  DATABASE_URL       postgresql://utilisateur@hote:5432/colis (sinon SQLite)
  DB_PASSWORD        mot de passe de la base (déconseillé)
  DB_PASSWORD_FILE   fichier qui contient le mot de passe (secret Compose ou Kubernetes)
  COLIS_DONNEES      dossier du fichier SQLite (défaut /donnees)
"""
import os
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)
URL = os.environ.get("DATABASE_URL", "")
DONNEES = os.environ.get("COLIS_DONNEES", "/donnees")
STATUTS = {"en preparation", "en transit", "livre", "retour"}


def mot_de_passe():
    f = os.environ.get("DB_PASSWORD_FILE")
    if f:
        with open(f) as h:
            return h.read().strip()
    return os.environ.get("DB_PASSWORD", "")


def connexion():
    if URL.startswith("postgres"):
        import psycopg
        return psycopg.connect(URL, password=mot_de_passe(), connect_timeout=5), "%s"
    os.makedirs(DONNEES, exist_ok=True)
    return sqlite3.connect(os.path.join(DONNEES, "colis.db")), "?"


def init():
    c, _ = connexion()
    c.execute("CREATE TABLE IF NOT EXISTS colis (numero TEXT PRIMARY KEY, destination TEXT NOT NULL, statut TEXT NOT NULL)")
    c.commit()
    c.close()


def base():
    return "postgres" if URL.startswith("postgres") else "sqlite"


@app.get("/sante")
def sante():
    try:
        init()
        return jsonify(etat="ok", base=base())
    except Exception as e:
        return jsonify(etat="erreur", base=base(), detail=str(e)[:200]), 503


@app.get("/colis")
def liste():
    init()
    c, _ = connexion()
    lignes = c.execute("SELECT numero, destination, statut FROM colis ORDER BY numero").fetchall()
    c.close()
    return jsonify([{"numero": n, "destination": d, "statut": s} for n, d, s in lignes])


@app.get("/colis/<numero>")
def un(numero):
    init()
    c, p = connexion()
    l = c.execute(f"SELECT numero, destination, statut FROM colis WHERE numero = {p}", (numero,)).fetchone()
    c.close()
    if not l:
        return jsonify(erreur="colis inconnu"), 404
    return jsonify(numero=l[0], destination=l[1], statut=l[2])


@app.post("/colis")
def creer():
    d = request.get_json(silent=True) or {}
    numero, dest, statut = d.get("numero"), d.get("destination"), d.get("statut", "en preparation")
    if not numero or not dest or statut not in STATUTS:
        return jsonify(erreur="numero, destination et statut valide attendus"), 400
    init()
    c, p = connexion()
    try:
        c.execute(f"INSERT INTO colis (numero, destination, statut) VALUES ({p}, {p}, {p})", (numero, dest, statut))
        c.commit()
    except Exception:
        c.close()
        return jsonify(erreur="numero deja present"), 409
    c.close()
    return jsonify(numero=numero, destination=dest, statut=statut), 201


@app.get("/")
def accueil():
    return jsonify(service="Suivi Colis", entreprise="Mistral Logistique", hote=os.uname().nodename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
