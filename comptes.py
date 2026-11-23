""" Gestion des comptes utilisateurs """
import hashlib
import re

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

bp_comptes = Blueprint("comptes", __name__, url_prefix="/comptes")


def valider_courriel(courriel):
    """Verifie si le courriel est valide"""
    if not courriel:
        return False

    regex_courriel = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(regex_courriel, courriel) is not None


def valider_mot_de_passe(mdp):
    """
    Mot de passe : min 8 caracteres, 1 maj, 1 min, 1 chiffre
    """
    if len(mdp) < 8:
        return False
    if not re.search(r"[A-Z]", mdp):
        return False
    if not re.search(r"[a-z]", mdp):
        return False
    if not re.search(r"[0-9]", mdp):
        return False
    return True


@bp_comptes.route("/connexion", methods=["GET", "POST"])
def connexion():
    """Page de connexion"""

    courriel = ""
    classe_courriel = ""
    classe_mot_de_passe = ""
    erreur_connexion = False

    if request.method == "POST":

        courriel = request.form.get("courriel", "").strip()
        mot_de_passe = request.form.get("mot_de_passe", "")

        erreurs = False

        if not courriel:
            classe_courriel = "is-invalid"
            erreurs = True

        if not mot_de_passe:
            classe_mot_de_passe = "is-invalid"
            erreurs = True

        if not erreurs:

            hash_mdp = hashlib.sha512(
                mot_de_passe.encode()
            ).hexdigest()

            with bd.creer_connexion() as conn:
                utilisateur = bd.get_utilisateur_par_courriel(
                    conn,
                    courriel
                )

            if (
                utilisateur is None
                or utilisateur["mot_de_passe"] != hash_mdp
            ):
                erreur_connexion = True
            else:
                session["id"] = utilisateur["id"]
                session["courriel"] = utilisateur["courriel"]
                session["role"] = utilisateur["role"]
                session.permanent = True

                flash("Connexion reussie.", "success")
                return redirect("/")

    return render_template(
        "comptes/connexion.jinja",
        courriel=courriel,
        classe_courriel=classe_courriel,
        classe_mot_de_passe=classe_mot_de_passe,
        erreur_connexion=erreur_connexion
    )


@bp_comptes.route("/deconnexion")
def deconnexion():
    """Deconnecte l'utilisateur"""
    session.clear()
    flash("Vous etes deconnecte.", "success")
    return redirect("/")


@bp_comptes.route("/ajouter", methods=["GET", "POST"])
def ajouter_utilisateur():
    """Ajoute un nouvel utilisateur (admin seulement)"""

    administrateur()

    courriel = ""
    credit = "0"
    erreurs = {}

    if request.method == "POST":

        courriel = request.form.get("courriel", "").strip()
        mot_de_passe = request.form.get("mot_de_passe", "")
        confirmation = request.form.get("confirmation", "")
        credit_str = request.form.get("credit", "0").strip()

        # Validation
        if not valider_courriel(courriel):
            erreurs["courriel"] = "Courriel invalide."

        if not valider_mot_de_passe(mot_de_passe):
            erreurs["mot_de_passe"] = (
                "Le mot de passe doit contenir au moins 8 caracteres, "
                "une majuscule, une minuscule et un chiffre."
            )

        if mot_de_passe != confirmation:
            erreurs["confirmation"] = "Les mots de passe ne correspondent pas."

        try:
            credit = float(credit_str)
            if credit < 0:
                erreurs["credit"] = "Le credit ne peut pas etre negatif."
        except ValueError:
            erreurs["credit"] = "Le credit doit etre un nombre."
            credit = 0

        # Verifier si le courriel existe deja
        if "courriel" not in erreurs:
            with bd.creer_connexion() as conn:
                existant = bd.get_utilisateur_par_courriel(conn, courriel)
            if existant is not None:
                erreurs["courriel"] = "Ce courriel est deja utilise."

        if not erreurs:

            hash_mdp = hashlib.sha512(
                mot_de_passe.encode()
            ).hexdigest()

            with bd.creer_connexion() as conn:
                bd.ajouter_utilisateur(
                    conn,
                    courriel=courriel,
                    mot_de_passe=hash_mdp,
                    credit=credit,
                    role="collectionneur"
                )

            flash("Utilisateur ajoute avec succes.", "success")
            return redirect(url_for("comptes.liste_utilisateurs"))

    return render_template(
        "comptes/ajouter.jinja",
        courriel=courriel,
        credit=credit,
        erreurs=erreurs
    )

@bp_comptes.route("/liste")
def liste_utilisateurs():
    """Liste tous les utilisateurs (admin seulement)"""

    administrateur()

    with bd.creer_connexion() as conn:
        utilisateurs = bd.get_collectionneurs(conn)

    return render_template(
        "comptes/liste.jinja",
        utilisateurs=utilisateurs
    )


@bp_comptes.route("/supprimer/<int:id_utilisateur>")
def supprimer_utilisateur(id_utilisateur):
    """Supprime un utilisateur (admin seulement)"""

    administrateur()

    if id_utilisateur == 1 or id_utilisateur == session.get("id"):
        flash("Impossible de supprimer ce compte.", "danger")
        return redirect(url_for("comptes.liste_utilisateurs"))

    with bd.creer_connexion() as conn:
        utilisateur = bd.get_utilisateur(conn, id_utilisateur)

        if utilisateur is None:
            abort(404)

        bd.supprimer_utilisateur(conn, id_utilisateur)

    flash("Utilisateur supprime.", "success")
    return redirect(url_for("comptes.liste_utilisateurs"))
