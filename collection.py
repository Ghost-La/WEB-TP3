from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    redirect,
    abort,
    session,
    url_for
)
import bd
from auth import utilisateur_connecte

bp_collection = Blueprint("collection", __name__, url_prefix="/collection")

ETATS_VALIDES = [
    "Presque neuve",
    "Légèrement usée",
    "Modérément usée",
    "Très usée",
    "Abîmée"
]

STATUTS_VALIDES = [
    "Disponible",
    "Recherchée"
]

@bp_collection.route("/")
def collection():

    utilisateur_connecte()

    with bd.creer_connexion() as conn:

        if session["role"] == "admin":

            cartes = bd.get_cartes_collection(conn)

        else:

            cartes = bd.get_cartes_collection(
                conn,
                id_collectionneur=session["id"]
            )

    return render_template(
        "collection/collection.jinja",
        cartes=cartes
    )

@bp_collection.route("/detail/<int:id_collection>")
def detail(id_collection):
    """Détail d'une carte"""

    with bd.creer_connexion() as conn:

        carte = bd.get_element_collection(
            conn,
            id_collection
        )

        carte["nom_collectionneur"] = bd.get_courriel_utilisateur(
            conn,
            carte["id_collectionneur"]
        )

    if carte is None:
        abort(404)

    return render_template(
        "collection/detail.jinja",
        carte=carte
    )

@bp_collection.route("/recherche",methods=["GET", "POST"])
def recherche():
    """Recherche de cartes"""

    cartes = []
    erreur = None
    nom = ""

    if request.method == "POST":

        nom = request.form.get("nom", "").strip()

        if len(nom) < 2:

            erreur = (
                "Le nom doit contenir "
                "au moins 2 caractères."
            )


        else:

            with bd.creer_connexion() as conn:

                cartes = bd.rechercher_cartes(conn, nom)

            if not cartes:
                erreur = "Aucune carte trouvée."

    return render_template(
        "collection/recherche.jinja",
        cartes=cartes,
        erreur=erreur,
        nom=nom
    )



@bp_collection.route("/ajouter/<string:id_carte>", methods=["GET", "POST"])
def ajout_carte(id_carte):
    """Ajouter une carte à sa collection"""

    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        carte = bd.get_carte_catalogue(conn, id_carte)

    if carte is None:
        abort(404)

    erreurs = {}

    if request.method == "POST":

        etat = request.form.get(
            "etat",
            ""
        ).strip()

        cout = request.form.get(
            "cout",
            ""
        ).strip()

        statut = request.form.get(
            "statut",
            ""
        ).strip()

        if etat not in ETATS_VALIDES:
            erreurs["etat"] = "État invalide."

        try:

            cout = float(cout)

            if cout < 0:
                erreurs["cout"] = (
                    "Le coût doit être positif."
                )

        except ValueError:

            erreurs["cout"] = (
                "Le coût doit être numérique."
            )

            cout = 0

        if statut not in STATUTS_VALIDES:

            erreurs["statut"] = (
                "Statut invalide."
            )

        else:

            statut = (
                1
                if statut == "Disponible"
                else 0
            )

        nom_photo = None

        photo = request.files.get("photo")

        if photo and photo.filename:

            if (
                len(photo.filename) < 6
                or len(photo.filename) > 50
            ):

                erreurs["photo"] = (
                    "Le nom du fichier doit contenir "
                    "entre 6 et 50 caractères."
                )

            else:

                nom_original = secure_filename(photo.filename)

                extension = os.path.splitext(nom_original)[1]
                
                nom_photo = (
                    uuid.uuid4().hex[:8]
                    + extension
                )

                chemin = os.path.join(
                    "static",
                    "images",
                    "ajouts",
                    nom_photo
                )

                photo.save(chemin)

        if not erreurs:

            with bd.creer_connexion() as conn:

                bd.ajouter_carte(
                    conn,
                    id_carte=id_carte,
                    id_collectionneur=session["id"],
                    date_ajout=datetime.now(),
                    etat=etat,
                    cout=cout,
                    statut=statut,
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

    return render_template(
        "collection/ajout.jinja",
        carte=carte,
        erreurs=erreurs
    )


@bp_collection.route("/modifier/<int:id_collection>", methods=["GET", "POST"])
def modification(id_collection):
    """Modifier une carte de sa collection"""

    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        carte = bd.get_element_collection(conn, id_collection)

    if carte is None:
        abort(404)

    if (
        carte["id_collectionneur"] != session["id"]
        and session.get("role") != "admin"
    ):
        abort(403)

    with bd.creer_connexion() as conn:
        if (
            session.get("role") != "admin"
            and bd.a_des_offres_en_attente(conn, id_collection)
        ):
            flash("Impossible de modifier : des offres sont en attente.", "danger")
            return redirect(url_for("collection.collection"))
        
    erreurs = {}

    if request.method == "POST":

        etat = request.form.get("etat", "").strip()
        cout = request.form.get("cout", "").strip()
        statut = request.form.get("statut", "").strip()

        if etat not in ETATS_VALIDES:
            erreurs["etat"] = "État invalide."

        try:
            cout = float(cout)
            if cout < 0:
                erreurs["cout"] = "Le coût doit être positif."
        except ValueError:
            erreurs["cout"] = "Le coût doit être numérique."
            cout = 0

        if statut not in STATUTS_VALIDES:
            erreurs["statut"] = "Statut invalide."
        else:
            statut = 1 if statut == "Disponible" else 0

        if not erreurs:
            with bd.creer_connexion() as conn:
                bd.modifier_carte(
                    conn,
                    id_collection,
                    etat,
                    cout,
                    statut
                )

            flash("Carte modifiée avec succès.", "success")
            return redirect("/collection", code=303)

    return render_template(
        "collection/modification.jinja",
        carte=carte,
        erreurs=erreurs
    )


@bp_collection.route("/supprimer/<int:id_collection>")
def supprimer(id_collection):
    """Supprimer une carte de sa collection"""

    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        carte = bd.get_element_collection(conn, id_collection)

        if carte is None:
            abort(404)

        if (
            carte["id_collectionneur"] != session["id"]
            and session.get("role") != "admin"
        ):
            abort(403)

        bd.supprimer_carte(conn, id_collection)

    flash("Carte supprimee.", "success")
    return redirect("/collection", code=303)

@bp_collection.route("/offre/<int:id_collection>", methods=["GET", "POST"])
def faire_offre(id_collection):
    """Faire une offre sur une carte"""
    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        carte = bd.get_element_collection(conn, id_collection)

    if carte is None:
        abort(404)

    if carte["id_collectionneur"] == session["id"]:
        abort(400)

    if carte["statut"] != 1:
        flash("Cette carte n'est pas disponible.", "danger")
        return redirect(url_for("collection.collection"))

    erreurs = {}
    montant = ""

    if request.method == "POST":
        montant = request.form.get("montant", "").strip()

        try:
            montant_val = float(montant)
            if montant_val <= 0:
                erreurs["montant"] = "Le montant doit etre positif."
        except ValueError:
            erreurs["montant"] = "Le montant doit etre un nombre."
            montant_val = 0

        with bd.creer_connexion() as conn:
            acheteur = bd.get_utilisateur(conn, session["id"])

        if not erreurs and acheteur["credit"] < montant_val:
            erreurs["montant"] = "Credit insuffisant."

        if not erreurs:
            with bd.creer_connexion() as conn:
                bd.creer_offre(
                    conn,
                    id_elem_collection=id_collection,
                    id_collectionneur=session["id"],
                    prix_offert=montant_val
                )

            flash("Offre envoyee.", "success")
            return redirect(url_for("collection.collection"), code=303)

    return render_template(
        "collection/faire_offre.jinja",
        carte=carte,
        montant=montant,
        erreurs=erreurs
    )


@bp_collection.route("/offres")
def liste_offres():
    """Liste des offres faites et reçues"""
    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        offres = bd.get_offres_pour_collectionneur(conn, session["id"])

    return render_template("collection/offres.jinja", offres=offres)


@bp_collection.route("/offres/accepter/<int:id_offre>")
def accepter_offre(id_offre):
    """Accepter une offre"""
    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        offre = bd.get_offre(conn, id_offre)

        if offre is None:
            abort(404)

  
        if offre["statut"] != "en attente":
            flash("Cette offre n'est plus en attente.", "danger")
            return redirect(url_for("collection.liste_offres"))


        carte = bd.get_element_collection(conn, offre["id_elem_collection"])

        if carte is None:
            abort(404)


        if carte["id_collectionneur"] != session["id"]:
            abort(403)

        acheteur = bd.get_utilisateur(conn, offre["id_collectionneur"])
        vendeur = bd.get_utilisateur(conn, carte["id_collectionneur"])

        montant = float(offre["prix_offert"])

        if acheteur["credit"] < montant:
            flash("L'acheteur n'a plus assez de credit.", "danger")
            return redirect(url_for("collection.liste_offres"))

        bd.maj_credit(conn, acheteur["id"], float(acheteur["credit"]) - montant)
        bd.maj_credit(conn, vendeur["id"], float(vendeur["credit"]) + montant)

        bd.changer_collectionneur(conn, carte["id"], offre["id_collectionneur"])
        bd.maj_statut_offre(conn, id_offre, "acceptée")

    flash("Offre acceptee. La carte a change de proprietaire.", "success")
    return redirect(url_for("collection.liste_offres"), code=303)


@bp_collection.route("/offres/refuser/<int:id_offre>")
def refuser_offre(id_offre):
    """Refuser une offre"""
    utilisateur_connecte()

    with bd.creer_connexion() as conn:
        offre = bd.get_offre(conn, id_offre)

        if offre is None:
            abort(404)

        if offre["statut"] != "en attente":
            flash("Cette offre n'est plus en attente.", "danger")
            return redirect(url_for("collection.liste_offres"))

        carte = bd.get_element_collection(conn, offre["id_elem_collection"])

        if carte is None:
            abort(404)

        if carte["id_collectionneur"] != session["id"]:
            abort(403)

        bd.maj_statut_offre(conn, id_offre, "refusée")

    flash("Offre refusee.", "success")
    return redirect(url_for("collection.liste_offres"), code=303)

