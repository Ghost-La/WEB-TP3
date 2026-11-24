"""API pour les fonctionnalités AJAX et les requêtes côté client."""
from datetime import datetime
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
from auth import utilisateur_connecte, administrateur, est_connecte, est_admin
import bd
import hashlib
import re
from werkzeug.exceptions import HTTPException
from flask import jsonify
from auth import administrateur


bp_api = Blueprint("api", __name__, url_prefix="/api")

@bp_api.route("/suggestions")
def suggestions():
    """Retourne des suggestions de noms à partir de 2 caractères."""
    terme = request.args.get("q", "").strip()
    if len(terme) < 2:
        return jsonify([])

    with bd.creer_connexion() as conn:
        resultats = bd.rechercher_suggestions(conn, terme)

    return jsonify(resultats)


@bp_api.route("/verifier-courriel")
def verifier_courriel():
    """Vérifie si un courriel existe déjà en base de données."""
    if not est_admin():
        return jsonify({"erreur": "Non autorisé"}), 403

    courriel = request.args.get("courriel", "").strip().lower()
    if not courriel:
        return jsonify({"existe": False})

    with bd.creer_connexion() as conn:
        utilisateur = bd.get_utilisateur_par_courriel(conn, courriel)

    return jsonify({"existe": utilisateur is not None})


@bp_api.route("/verifier-montant")
def verifier_montant():
    """Vérifie que l'offre est strictement supérieure au coût de la carte."""
    if not est_connecte():
        return jsonify({"valide": False, "message": "Authentification requise"}), 401

    try:
        id_collection = int(request.args.get("id_collection"))
        montant = float(request.args.get("montant", 0))
    except (TypeError, ValueError):
        return jsonify({"valide": False, "message": "Données invalides"}), 400

    with bd.creer_connexion() as conn:
        carte = bd.get_element_collection(conn, id_collection)
        if carte is None or carte.get("supprime") == 1:
            return jsonify({"valide": False, "message": "Carte introuvable"}), 404

    cout = float(carte["cout"])
    if montant <= cout:
        return jsonify({
            "valide": False,
            "message": f"Le montant doit être supérieur à {cout:.2f} $"
        })

    return jsonify({"valide": True, "message": "Montant acceptable"})


@bp_api.route("/utilisateurs/<int:id_utilisateur>", methods=["DELETE"])
def supprimer_utilisateur_api(id_utilisateur):
    """Suppression logique (soft delete) d'un utilisateur."""
    administrateur()

    if session.get("id") == id_utilisateur:
        return jsonify({"erreur": "Impossible de vous supprimer vous-même"}), 400

    with bd.creer_connexion() as conn:
        utilisateur = bd.get_utilisateur(conn, id_utilisateur)
        if utilisateur is None or utilisateur.get("supprime") == 1:
            return jsonify({"erreur": "Utilisateur introuvable"}), 404

        bd.soft_delete_utilisateur(conn, id_utilisateur)

    return jsonify({"succes": True})


@bp_api.route("/cartes/<int:id_collection>", methods=["DELETE"])
def supprimer_carte_api(id_collection):
    """Suppression logique (soft delete) d'une carte."""
    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        carte = bd.get_element_collection(conn, id_collection)
        if carte is None or carte.get("supprime") == 1:
            return jsonify({"erreur": "Carte introuvable"}), 404

        if session.get("role") != "admin" and carte["id_collectionneur"] != session["id"]:
            return jsonify({"erreur": "Action interdite"}), 403

        bd.soft_delete_carte(conn, id_collection)

    return jsonify({"succes": True})


@bp_api.route("/cartes")
def liste_cartes_api():
    """Retourne une page de cartes pour le défilement infini et le polling."""
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 6))
    except ValueError:
        return jsonify({"erreur": "Paramètres invalides"}), 400

    filtre = request.args.get("filtre")
    recherche = request.args.get("recherche", "").strip()
    est_collection = request.args.get("collection") == "1"

    id_collectionneur = None
    if est_collection:
        if not est_connecte():
            return jsonify({"erreur": "Authentification requise"}), 401
        if session.get("role") != "admin":
            id_collectionneur = session["id"]

    with bd.creer_connexion() as conn:
        cartes = bd.get_cartes_pour_api(
            conn,
            filtre=filtre,
            id_collectionneur=id_collectionneur,
            offset=offset,
            limit=limit,
            recherche=recherche if len(recherche) >= 2 else None
        )

    resultats = []
    for c in cartes:
        resultats.append({
            "id_collection": c["id_collection"],
            "nom": c["nom"],
            "supertype": c.get("supertype"),
            "rarete": c.get("rarete"),
            "etat": c.get("etat"),
            "cout": float(c["cout"]) if c.get("cout") is not None else None,
            "statut": c.get("statut"),
            "photo": c.get("photo"),
            "date_ajout": c["date_ajout"].isoformat() if c.get("date_ajout") else None
        })

    return jsonify({
        "cartes": resultats,
        "offset": offset,
        "limit": limit,
        "has_more": len(resultats) == limit
    })

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
    
@bp_api.route("/recherche-carte")
def recherche_carte():
    mots_cles = request.args.get("mots-cles", default="")
    
    with bd.creer_connexion() as conn:
        cartes = bd.recherche_carte(conn, mots_cles)
    return jsonify(cartes)    


@bp_api.route("ajout-envie/<id_carte>")
def ajout_envie(id_carte):
    ''''''
    """Ajouter une carte aux envies"""
 
    message = {"message": "Carte ajoutée à vos envies"}
    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        carte = bd.get_carte_catalogue(conn, id_carte)

    if carte is None:
        abort(404)

    erreurs = {}

    if request.method == "POST":

        etat = "Presque neuve"

        cout = 0

        statut = "Recherchée"
            

        nom_photo = None

        photo = request.files.get("photo")

        

        if not erreurs:

            with bd.creer_connexion() as conn:

                bd.ajouter_carte(
                    conn,
                    id_carte=id_carte,
                    id_collectionneur=session["id"],
                    date_ajout=datetime.now(),
                    etat=etat,
                    cout=cout,
                    statut= statut,
                    photo=nom_photo
                )

            flash(
                "Carte ajoutée à votre collection.",
                "success"
            )

            return redirect(
                url_for("collection.collection"),
                code=303
            )
            return jsonify(message) 

    return render_template(
        "collection/ajout-envie.jinja",
        carte=carte,
        erreurs=erreurs
    ) 
    
   


  

