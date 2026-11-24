import hashlib
import re
from werkzeug.exceptions import HTTPException
from flask import jsonify

from flask import (
    abort,
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for
)
import bd
from auth import administrateur

bp_api = Blueprint("api", __name__, url_prefix="/api")

@bp_api.route("/recherche-collection")
def recherche_collection():
    mots_cles = request.args.get("mots-cles", default="")
    
    with bd.creer_connexion() as conn:
        cartes = bd.rechercher_cartes_collection(conn, mots_cles)
    return jsonify(cartes)    

@bp_api.route("/valider-offre")

def valider_offre():
    montant = request.args.get("montant", type= float)
    prix = request.args.get("prix", type=float)
    
    return jsonify({"valide": montant > prix})

@bp_api.route(
    "/supprimer-carte/<int:id_collection>",
    methods=["DELETE"]
)

def supprimer_carte(id_collection):

    with bd.creer_connexion() as conn:

        bd.supprimer_carte(
            conn,
            id_collection
        )

    return jsonify({
        "succes": True
    })
    
@bp_api.errorhandler(
    HTTPException
)
def gerer_erreur_http(e):

    return jsonify(
        {
            "code": e.code,
            "nom": e.name,
            "description": e.description
        }
    ), e.code    