""" Application Flask pour la gestion de la collection de cartes Pokémon """

from flask import Flask
from flask import render_template
from flask import session
from flask import request
from dotenv import load_dotenv

from comptes import bp_comptes
from collection import bp_collection

import os
import bd

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")

app.register_blueprint(bp_comptes)
app.register_blueprint(bp_collection)
app.register_blueprint(api.bp_api)

app.config["CHEMIN_VERS_AJOUTS"] = "static/images/ajouts"

@app.route("/")
def index():
    """Page d'accueil avec les cartes recentes"""
    filtre = request.args.get("filtre", "disponibles")
    with bd.creer_connexion() as conn:
        if filtre == "recherchees" and "id" in session:
            cartes = bd.get_cartes_collection(conn, statut = 0)
        elif filtre == "disponibles" and "id" in session:
            cartes = bd.get_cartes_collection(conn, statut = 1)
        else:
            cartes = bd.get_cartes_collection(conn)

    return render_template(
        "index.jinja",
        cartes=cartes,
        filtre=filtre
    )


@app.errorhandler(400)
def erreur_400(e):
    """Gere les erreurs 400 (Bad Request)"""
    return render_template("erreurs/400.jinja"), 400


@app.errorhandler(401)
def erreur_401(e):
    """Gere les erreurs 401 (Unauthorized)"""
    return render_template("erreurs/401.jinja"), 401


@app.errorhandler(403)
def erreur_403(e):
    """Gere les erreurs 403 (Forbidden)"""
    return render_template("erreurs/403.jinja"), 403


@app.errorhandler(404)
def erreur_404(e):
    """Gere les erreurs 404 (Not Found)"""
    return render_template("erreurs/404.jinja"), 404


@app.errorhandler(500)
def erreur_500(e):
    """Gere les erreurs 500 (Internal Server Error)"""
    return render_template("erreurs/500.jinja"), 500


if __name__ == "__main__":
    app.run(debug=True)
